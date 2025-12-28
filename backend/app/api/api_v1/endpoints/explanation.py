from fastapi import APIRouter, Query, Body, Depends, HTTPException
from fastapi.responses import StreamingResponse
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from app.services.explanation_service import ExplanationService
from app.adapters.neo4j_adapter import Neo4jAdapter
from app.core.llm import llm_service
from app.services.conversation_service import conversation_service
from app.api.api_v1.endpoints.auth import get_current_user
import logging
import json
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter()

# Dependency Injection - 使用真实 LLM
graph_db = Neo4jAdapter()

# 创建真实的 LLM Provider
class RealLLMProvider:
    """真实的 LLM Provider，不使用 Mock"""
    
    async def generate(self, prompt: str, schema: Dict[str, Any] = None) -> str:
        client = llm_service.get_client()
        if not client:
            raise HTTPException(
                status_code=503,
                detail="LLM 服务不可用，请检查 OPENAI_API_KEY 配置"
            )
        
        try:
            response = await client.chat.completions.create(
                model=llm_service.get_model_name(),
                messages=[
                    {"role": "system", "content": "你是一位专业的医保政策助手。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise HTTPException(
                status_code=503,
                detail=f"LLM 调用失败: {str(e)}"
            )
    
    async def generate_stream(self, prompt: str):
        """流式生成，逐步返回内容"""
        try:
            async for chunk in llm_service.generate_stream(prompt):
                yield chunk
        except Exception as e:
            logger.error(f"Streaming generation failed: {e}")
            raise

llm_provider = RealLLMProvider()
explanation_service = ExplanationService(graph_db, llm_provider)


class Message(BaseModel):
    """对话消息模型"""
    role: str  # 'user' or 'ai'
    content: str
    

class QueryRequest(BaseModel):
    """查询请求模型"""
    question: str
    session_id: Optional[str] = None
    use_history: bool = True  # 是否使用历史对话


@router.post("/query")
async def query_policy(
    request: QueryRequest = Body(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Answer policy-related questions with conversation history support.
    Non-streaming version for backward compatibility.
    """
    
    # 检查 LLM 是否可用
    if not llm_service.get_client():
        raise HTTPException(
            status_code=503,
            detail="LLM 服务不可用。请在系统配置中设置 OPENAI_API_KEY 和 OPENAI_BASE_URL"
        )
    
    # 获取或创建会话
    session_id = request.session_id
    if not session_id:
        # 创建新对话
        conversation = conversation_service.create_conversation(
            user_id=current_user["username"],
            title=request.question[:30] + "..." if len(request.question) > 30 else request.question
        )
        session_id = conversation["session_id"]
        logger.info(f"Created new conversation: {session_id}")
    
    # 获取对话历史
    conversation_history = []
    if request.use_history:
        conversation_history = conversation_service.get_conversation_context(
            session_id, 
            max_turns=5  # 最多保留5轮对话
        )
    
    logger.info(f"Query with session_id={session_id}, history_len={len(conversation_history)}")
    
    # 保存用户消息
    conversation_service.add_message(
        session_id=session_id,
        role="user",
        content=request.question
    )
    
    try:
        # 调用增强的查询服务
        result = await explanation_service.query_policy(
            question=request.question,
            conversation_history=conversation_history,
            session_id=session_id
        )
        
        # 保存 AI 回复
        conversation_service.add_message(
            session_id=session_id,
            role="ai",
            content=result["answer"],
            metadata={
                "sources": result.get("sources", []),
                "reasoning_trace": result.get("reasoning_trace", []),
                "entities": result.get("entities", [])
            }
        )
        
        # 添加 session_id 到响应
        result["session_id"] = session_id
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"查询处理失败: {str(e)}"
        )


@router.post("/query-stream")
async def query_policy_stream(
    request: QueryRequest = Body(...),
    current_user: dict = Depends(get_current_user)
):
    """
    流式问答接口 - 实时返回思考过程和答案，提升用户体验
    
    返回格式（Server-Sent Events）：
    - data: {"type": "metadata", "data": {...}}  # 推理元数据
    - data: {"type": "thinking", "content": "..."}  # 思考过程片段
    - data: {"type": "thinking_done"}  # 思考完成
    - data: {"type": "chunk", "content": "..."}  # 答案片段
    - data: {"type": "done", "session_id": "..."}  # 结束标记
    """
    
    # 检查 LLM 是否可用
    if not llm_service.get_client():
        raise HTTPException(
            status_code=503,
            detail="LLM 服务不可用"
        )
    
    # 获取或创建会话
    session_id = request.session_id
    if not session_id:
        conversation = conversation_service.create_conversation(
            user_id=current_user["username"],
            title=request.question[:30] + "..." if len(request.question) > 30 else request.question
        )
        session_id = conversation["session_id"]
    
    # 获取对话历史
    conversation_history = []
    if request.use_history:
        conversation_history = conversation_service.get_conversation_context(
            session_id, 
            max_turns=5
        )
    
    # 保存用户消息
    conversation_service.add_message(
        session_id=session_id,
        role="user",
        content=request.question
    )
    
    async def event_generator():
        """生成 SSE 事件流"""
        try:
            # 执行推理流程（不生成答案）
            result = await explanation_service.query_policy_prepare(
                question=request.question,
                conversation_history=conversation_history,
                session_id=session_id
            )
            
            # 先发送元数据（推理链路、来源等）
            metadata = {
                "type": "metadata",
                "data": {
                    "session_id": session_id,
                    "reasoning_trace": result.get("reasoning_trace", []),
                    "sources": result.get("sources", []),
                    "entities": result.get("entities", [])
                }
            }
            yield f"data: {json.dumps(metadata, ensure_ascii=False)}\n\n"
            
            # === 思考过程阶段 ===
            # 构建思考过程的 prompt
            thinking_prompt = f"""
请分析以下问题，并展示你的思考过程：

问题：{result.get('contextualized_question', request.question)}

已检索到的相关政策规则：
{json.dumps(result.get('sources', [])[:3], ensure_ascii=False, indent=2)}

识别的实体：
{json.dumps(result.get('entities', []), ensure_ascii=False)}

请按照以下步骤思考（简洁）：
1. 问题理解：这个问题的核心是什么？
2. 信息分析：检索到的政策规则是否相关？
3. 推理逻辑：如何组织答案？
4. 关键要点：需要特别强调的内容？

请用 200 字以内简明扼要地展示思考过程。
"""
            
            logger.info("[THINKING] Starting thinking process generation")
            yield f"data: {json.dumps({'type': 'thinking_start'}, ensure_ascii=False)}\n\n"
            
            full_thinking = ""
            chunk_count = 0
            async for chunk in llm_provider.generate_stream(thinking_prompt):
                full_thinking += chunk
                chunk_count += 1
                thinking_data = {
                    "type": "thinking",
                    "content": chunk
                }
                yield f"data: {json.dumps(thinking_data, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.01)
            
            logger.info(f"[THINKING] Completed. Total chunks: {chunk_count}, Total length: {len(full_thinking)}")
            yield f"data: {json.dumps({'type': 'thinking_done'}, ensure_ascii=False)}\n\n"
            
            # === 答案生成阶段 ===
            logger.info("[ANSWER] Starting answer generation")
            yield f"data: {json.dumps({'type': 'answer_start'}, ensure_ascii=False)}\n\n"
            
            full_answer = ""
            answer_chunk_count = 0
            async for chunk in llm_provider.generate_stream(result["prompt"]):
                full_answer += chunk
                answer_chunk_count += 1
                chunk_data = {
                    "type": "chunk",
                    "content": chunk
                }
                yield f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.01)
            
            logger.info(f"[ANSWER] Completed. Total chunks: {answer_chunk_count}, Total length: {len(full_answer)}")
            
            # 保存完整答案（包含思考过程）
            conversation_service.add_message(
                session_id=session_id,
                role="ai",
                content=full_answer,
                metadata={
                    "sources": result.get("sources", []),
                    "reasoning_trace": result.get("reasoning_trace", []),
                    "entities": result.get("entities", []),
                    "thinking": full_thinking  # 保存思考过程
                }
            )
            
            # 发送完成标记
            done_data = {
                "type": "done",
                "session_id": session_id,
                "full_answer": full_answer,
                "full_thinking": full_thinking
            }
            yield f"data: {json.dumps(done_data, ensure_ascii=False)}\n\n"
            
        except Exception as e:
            logger.error(f"Streaming query failed: {e}")
            error_data = {
                "type": "error",
                "error": str(e)
            }
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


# 保持向后兼容的简单查询接口
@router.get("/query-simple")
async def query_policy_simple(
    question: str = Query(..., description="用户问题"),
    current_user: dict = Depends(get_current_user)
):
    """
    简单查询接口（向后兼容，不支持多轮对话）
    """
    # 检查 LLM 是否可用
    if not llm_service.get_client():
        raise HTTPException(
            status_code=503,
            detail="LLM 服务不可用。请配置 OPENAI_API_KEY"
        )
    
    instruction = f"[CONTEXT: answer the policy question] {question}"
    
    # 创建临时会话
    conversation = conversation_service.create_conversation(
        user_id=current_user["username"],
        title=question[:30]
    )
    
    try:
        result = await explanation_service.query_policy(
            question=instruction,
            conversation_history=[],
            session_id=conversation["session_id"]
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Simple query failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"查询失败: {str(e)}"
        )
