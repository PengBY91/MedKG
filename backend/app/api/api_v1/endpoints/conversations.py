"""
对话历史管理 API
提供对话的增删改查、历史记录管理等功能
"""

from fastapi import APIRouter, Query, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from app.services.conversation_service import conversation_service
from app.api.api_v1.endpoints.auth import get_current_user

router = APIRouter()


class ConversationCreate(BaseModel):
    """创建对话请求"""
    title: Optional[str] = "新对话"


class ConversationUpdate(BaseModel):
    """更新对话请求"""
    title: Optional[str] = None


class ConversationResponse(BaseModel):
    """对话响应"""
    session_id: str
    user_id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int
    last_question: Optional[str] = None


@router.post("/conversations", response_model=dict)
async def create_conversation(
    request: ConversationCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    创建新对话
    """
    conversation = conversation_service.create_conversation(
        user_id=current_user["username"],
        title=request.title
    )
    
    return {
        "success": True,
        "data": {
            "session_id": conversation["session_id"],
            "title": conversation["title"],
            "created_at": conversation["created_at"]
        }
    }


@router.get("/conversations", response_model=dict)
async def list_conversations(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user)
):
    """
    获取对话列表
    """
    conversations = conversation_service.list_conversations(
        user_id=current_user["username"],
        limit=limit,
        offset=offset
    )
    
    # 格式化响应
    items = []
    for conv in conversations:
        items.append({
            "session_id": conv["session_id"],
            "title": conv["title"],
            "message_count": conv["metadata"].get("message_count", 0),
            "last_question": conv["metadata"].get("last_question"),
            "created_at": conv["created_at"],
            "updated_at": conv["updated_at"],
            "summary": conversation_service.generate_summary(conv["session_id"])
        })
    
    return {
        "success": True,
        "data": {
            "items": items,
            "total": len(items),
            "limit": limit,
            "offset": offset
        }
    }


@router.get("/conversations/{session_id}", response_model=dict)
async def get_conversation(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    获取对话详情
    """
    conversation = conversation_service.get_conversation(session_id)
    
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    # 验证权限
    if conversation["user_id"] != current_user["username"]:
        raise HTTPException(status_code=403, detail="无权访问此对话")
    
    return {
        "success": True,
        "data": conversation
    }


@router.get("/conversations/{session_id}/messages", response_model=dict)
async def get_conversation_messages(
    session_id: str,
    limit: int = Query(100, ge=1, le=500),
    current_user: dict = Depends(get_current_user)
):
    """
    获取对话消息列表
    """
    conversation = conversation_service.get_conversation(session_id)
    
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    # 验证权限
    if conversation["user_id"] != current_user["username"]:
        raise HTTPException(status_code=403, detail="无权访问此对话")
    
    messages = conversation_service.get_conversation_messages(session_id, limit=limit)
    
    return {
        "success": True,
        "data": {
            "session_id": session_id,
            "messages": messages,
            "total": len(messages)
        }
    }


@router.put("/conversations/{session_id}", response_model=dict)
async def update_conversation(
    session_id: str,
    request: ConversationUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    更新对话信息（如标题）
    """
    conversation = conversation_service.get_conversation(session_id)
    
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    # 验证权限
    if conversation["user_id"] != current_user["username"]:
        raise HTTPException(status_code=403, detail="无权修改此对话")
    
    # 更新标题
    if request.title:
        conversation["title"] = request.title
        conversation_service._save_to_disk()
    
    return {
        "success": True,
        "data": {
            "session_id": session_id,
            "title": conversation["title"]
        }
    }


@router.delete("/conversations/{session_id}", response_model=dict)
async def delete_conversation(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    删除对话
    """
    conversation = conversation_service.get_conversation(session_id)
    
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    # 验证权限
    if conversation["user_id"] != current_user["username"]:
        raise HTTPException(status_code=403, detail="无权删除此对话")
    
    success = conversation_service.delete_conversation(session_id)
    
    return {
        "success": success,
        "message": "对话已删除"
    }


@router.delete("/conversations", response_model=dict)
async def clear_conversations(
    current_user: dict = Depends(get_current_user)
):
    """
    清空当前用户的所有对话
    """
    count = conversation_service.clear_user_conversations(current_user["username"])
    
    return {
        "success": True,
        "message": f"已清空 {count} 个对话"
    }


@router.get("/conversations/{session_id}/summary", response_model=dict)
async def get_conversation_summary(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    获取对话摘要
    """
    conversation = conversation_service.get_conversation(session_id)
    
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    # 验证权限
    if conversation["user_id"] != current_user["username"]:
        raise HTTPException(status_code=403, detail="无权访问此对话")
    
    summary = conversation_service.generate_summary(session_id)
    
    return {
        "success": True,
        "data": {
            "session_id": session_id,
            "summary": summary
        }
    }

