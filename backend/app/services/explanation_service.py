from typing import Dict, Any, List
from app.core.interfaces import LLMProvider
from app.adapters.neo4j_adapter import Neo4jAdapter
from app.services.kag_solver_service import kag_solver_service
from app.services.prompt_builder import prompt_builder
from app.services.terminology_service import TerminologyService
from app.services.search_service import search_service
import json
import logging
import re

logger = logging.getLogger(__name__)

class ExplanationService:
    def __init__(self, graph_db: Neo4jAdapter, llm: LLMProvider):
        self.graph_db = graph_db
        self.llm = llm
        self.terminology_service = TerminologyService()
        self.search_service = search_service
    
    async def explain_rejection(self, patient_id: str, claim_id: str = None) -> Dict[str, Any]:
        """
        Generate explanation for claim rejection using GraphRAG.
        
        Steps:
        1. Retrieve patient subgraph from Neo4j
        2. Find rule violations
        3. Build evidence chain
        4. Generate natural language explanation via LLM
        """
        
        # Step 1: Retrieve subgraph
        subgraph = await self.graph_db.get_patient_subgraph(patient_id)
        if not subgraph:
            return {
                "status": "error",
                "message": f"Patient {patient_id} not found"
            }
        
        # Step 2: Find violations
        violations = await self.graph_db.find_violations(patient_id)
        if not violations:
            return {
                "status": "success",
                "message": "No violations found",
                "patient_id": patient_id
            }
        
        # Step 3: Build evidence chain
        evidence_chain = self._build_evidence_chain(subgraph, violations)
        
        # Step 4: Generate explanation
        explanation = await self._generate_explanation(evidence_chain)
        
        return {
            "status": "success",
            "patient_id": patient_id,
            "violations": violations,
            "evidence_chain": evidence_chain,
            "explanation": explanation
        }
    
    async def _build_evidence_chain(self, subgraph: Dict[str, Any], violations: list) -> str:
        """
        Build a structured evidence chain from graph data, including policy hierarchy.
        """
        chains = []
        patient = subgraph.get("patient", {})
        patient_info = f"患者: {patient.get('name', 'Unknown')} (ID: {patient.get('id', 'N/A')})"
        
        for violation in violations:
            treatment = violation["treatment"]
            rule = violation["rule"]
            
            # Fetch policy context from Graph
            context = await self.graph_db.get_policy_context(rule["id"])
            parent_doc = context.get("parent_doc", {})
            siblings = context.get("siblings", [])
            
            hierarchy_info = f"{parent_doc.get('level', '标准')} -> {parent_doc.get('name', '医疗保险规范')}"
            
            chain = f"""
{patient_info}
└─ 情况分析: {treatment['name']} 费用超出限额
   └─ 适用法律/规章: {hierarchy_info}
      └─ 具体规则: {rule['name']}
         ├─ 限额标准: {violation['expected']}元
         ├─ 实际发生: {violation['actual']}元
         └─ 违规类型: {violation['violation_type']}
   └─ 相关参考规则数: {len(siblings)}
   └─ 政策凭证: {violation['policy_reference']}
"""
            chains.append(chain)
        
        return "\n".join(chains)
    
    async def _generate_explanation(self, evidence_chain: str) -> str:
        """Use LLM to generate human-readable explanation."""
        prompt = f"""
你是一位医保合规审查官。请基于以下「决策证据链」，为患者或医疗机构生成一份专业的拒付理由陈述。

决策证据链:
{evidence_chain}

要求:
1. 说明费用的具体合规漏洞（例如：超过日均最高限额）。
2. 明确引用上位法或规章（如：结算管理规范）。
3. 给出建设性的后续建议（如：通过商业保险覆盖或调整治疗方案）。
4. 语言专业、严谨且具有说服力。

输出格式（纯文本）:
"""
        explanation = await self.llm.generate(prompt)
        return explanation.strip()
    
    async def query_policy(
        self, 
        question: str, 
        conversation_history: List[Dict[str, str]] = None,
        session_id: str = None
    ) -> Dict[str, Any]:
        """
        Simplified policy question answering pipeline (optimized for speed):
        1. Query Understanding (combined with context processing)
        2. Multi-channel Retrieval (Keyword + Vector only, no graph)
        3. KAG Logic Reasoning
        4. Knowledge Fusion & Generation
        
        Args:
            question: Current user question
            conversation_history: List of previous conversation turns
            session_id: Optional session identifier for tracking
        """
        logger.info(f"[Simplified QA Pipeline] Starting for: {question}")
        if conversation_history:
            logger.info(f"[Conversation Context] History length: {len(conversation_history)} turns")
        
        # ===== Stage 1: Query Understanding (with context) =====
        # 合并了 Stage 0 和 Stage 1，同时处理上下文和实体识别
        contextualized_question = await self._contextualize_query(question, conversation_history)
        entities, rewritten_query = await self._understand_query(contextualized_question)
        
        context_info = f"处理 {len(conversation_history)} 轮对话" if conversation_history else "单轮查询"
        logger.info(f"[Stage 1] {context_info}, 识别实体: {len(entities)}个")
        
        # ===== Stage 2: Simplified Retrieval (Keyword + Vector only) =====
        # 简化检索：只使用关键词和向量检索，移除图谱检索
        search_query = rewritten_query if rewritten_query else contextualized_question
        related_nodes = await self._simplified_retrieval(search_query, top_k=8)
        logger.info(f"[Stage 2] Retrieved {len(related_nodes)} policy rules (keyword+vector only)")
        
        # ===== Stage 3: KAG Logic Reasoning =====
        # 直接使用检索结果，不做重排序
        kag_context = {
            "rules": related_nodes[:5],
            "entities": entities,
            "conversation_history": conversation_history[-2:] if conversation_history else []
        }
        kag_result = await kag_solver_service.solve_query(search_query, context=kag_context)
        kag_answer = kag_result.get("answer") if "error" not in kag_result else None
        logger.info(f"[Stage 3] KAG reasoning: {'Success' if kag_answer else 'No result'}")
        
        # ===== Stage 4: Knowledge Fusion & Generation =====
        # 构建简化的 prompt
        prompt = prompt_builder.build_policy_qa_prompt(
            question=contextualized_question,
            retrieved_rules=related_nodes,
            kag_answer=kag_answer,
            entities=entities,
            standard_terms={}  # 不再做术语标准化
        )
        
        # 添加对话历史（如果有）
        if conversation_history:
            history_text = self._format_conversation_history(conversation_history[-3:])  # 只使用最近3轮
            prompt = f"【对话历史】\n{history_text}\n\n{prompt}"
        
        logger.info("[Stage 4] Generating answer with simplified prompt...")
        answer = await self.llm.generate(prompt)
        
        # ===== Build Simplified Reasoning Trace =====
        reasoning_trace = [
            {
                "step": "1. Query Understanding",
                "status": "Done",
                "detail": f"{context_info}，识别实体: {len(entities)}个, 查询改写: {'是' if rewritten_query else '否'}"
            },
            {
                "step": "2. Multi-channel Retrieval",
                "status": "Done",
                "detail": f"检索到 {len(related_nodes)} 条政策规则（关键词+向量）"
            },
            {
                "step": "3. KAG Logic Reasoning",
                "status": "Success" if kag_answer else "Skipped",
                "detail": "KAG 成功执行逻辑推理" if kag_answer else "KAG 未找到匹配逻辑"
            },
            {
                "step": "4. Knowledge Fusion",
                "status": "Done",
                "detail": "多源知识融合，生成最终答案"
            }
        ]
        
        return {
            "question": question,
            "contextualized_question": contextualized_question if conversation_history else None,
            "answer": answer,
            "sources": related_nodes,
            "entities": entities,
            "reasoning_trace": reasoning_trace,
            "kag_raw": kag_result,
            "metadata": {
                "pipeline_version": "simplified-v1-fast",
                "retrieval_count": len(related_nodes),
                "has_conversation_context": bool(conversation_history),
                "session_id": session_id
            }
        }
    
    async def query_policy_prepare(
        self,
        question: str,
        conversation_history: List[Dict[str, str]] = None,
        session_id: str = None
    ) -> Dict[str, Any]:
        """
        准备问答所需的所有数据，但不生成最终答案（用于流式响应）
        
        返回包含 prompt 和所有元数据的字典，供流式 API 使用
        """
        logger.info(f"[Prepare Pipeline] Starting for: {question}")
        
        # Stage 1: Query Understanding (with context)
        contextualized_question = await self._contextualize_query(question, conversation_history)
        entities, rewritten_query = await self._understand_query(contextualized_question)
        
        context_info = f"处理 {len(conversation_history)} 轮对话" if conversation_history else "单轮查询"
        logger.info(f"[Stage 1] {context_info}, 识别实体: {len(entities)}个")
        
        # Stage 2: Simplified Retrieval
        search_query = rewritten_query if rewritten_query else contextualized_question
        related_nodes = await self._simplified_retrieval(search_query, top_k=8)
        logger.info(f"[Stage 2] Retrieved {len(related_nodes)} policy rules")
        
        # Stage 3: KAG Logic Reasoning
        kag_context = {
            "rules": related_nodes[:5],
            "entities": entities,
            "conversation_history": conversation_history[-2:] if conversation_history else []
        }
        kag_result = await kag_solver_service.solve_query(search_query, context=kag_context)
        kag_answer = kag_result.get("answer") if "error" not in kag_result else None
        logger.info(f"[Stage 3] KAG reasoning: {'Success' if kag_answer else 'No result'}")
        
        # Stage 4: Build prompt (不调用 LLM)
        prompt = prompt_builder.build_policy_qa_prompt(
            question=contextualized_question,
            retrieved_rules=related_nodes,
            kag_answer=kag_answer,
            entities=entities,
            standard_terms={}
        )
        
        if conversation_history:
            history_text = self._format_conversation_history(conversation_history[-3:])
            prompt = f"【对话历史】\n{history_text}\n\n{prompt}"
        
        logger.info("[Stage 4] Prompt prepared for streaming generation")
        
        # Build reasoning trace
        reasoning_trace = [
            {
                "step": "1. Query Understanding",
                "status": "Done",
                "detail": f"{context_info}，识别实体: {len(entities)}个, 查询改写: {'是' if rewritten_query else '否'}"
            },
            {
                "step": "2. Multi-channel Retrieval",
                "status": "Done",
                "detail": f"检索到 {len(related_nodes)} 条政策规则（关键词+向量）"
            },
            {
                "step": "3. KAG Logic Reasoning",
                "status": "Success" if kag_answer else "Skipped",
                "detail": "KAG 成功执行逻辑推理" if kag_answer else "KAG 未找到匹配逻辑"
            },
            {
                "step": "4. Knowledge Fusion",
                "status": "Streaming",
                "detail": "流式生成答案中..."
            }
        ]
        
        return {
            "question": question,
            "contextualized_question": contextualized_question if conversation_history else None,
            "prompt": prompt,  # 供流式生成使用
            "sources": related_nodes,
            "entities": entities,
            "reasoning_trace": reasoning_trace,
            "kag_raw": kag_result,
            "metadata": {
                "pipeline_version": "simplified-v1-streaming",
                "retrieval_count": len(related_nodes),
                "has_conversation_context": bool(conversation_history),
                "session_id": session_id
            }
        }
    
    async def _contextualize_query(
        self, 
        question: str, 
        conversation_history: List[Dict[str, str]] = None
    ) -> str:
        """
        处理对话上下文，解析指代词并补全问题。
        
        例如：
        - 用户1: "门诊透析费用有限额吗？"
        - AI1: "是的，每日420元"
        - 用户2: "那糖尿病呢？" 
        - 解析后: "糖尿病门诊费用有限额吗？"
        """
        if not conversation_history or len(conversation_history) == 0:
            return question
        
        # 简单的指代识别（生产环境应使用更复杂的共指消解模型）
        指代词 = ["它", "这个", "那个", "这", "那", "呢", "的话"]
        
        has_reference = any(word in question for word in 指代词)
        
        if has_reference:
            # 获取最近一轮对话的主题
            last_user_msg = None
            for msg in reversed(conversation_history):
                if msg["role"] == "user":
                    last_user_msg = msg["content"]
                    break
            
            if last_user_msg:
                # 提取上一轮的关键实体
                logger.info(f"Contextualizing with last question: {last_user_msg}")
                # 简单实现：如果当前问题很短且有指代词，补充上文信息
                if len(question) < 15 and ("呢" in question or "那" in question):
                    # 提取主题词
                    for entity in ["透析", "糖尿病", "高血压", "CT", "MRI"]:
                        if entity in last_user_msg:
                            # 尝试替换
                            contextualized = question.replace("呢", "").replace("那", entity).strip()
                            if contextualized != question:
                                logger.info(f"Contextualized: '{question}' -> '{contextualized}'")
                                return contextualized
        
        return question
    
    def _format_conversation_history(self, conversation_history: List[Dict[str, str]]) -> str:
        """格式化对话历史为文本"""
        history_lines = []
        for msg in conversation_history[-3:]:  # 只保留最近3轮
            role_label = "用户" if msg["role"] == "user" else "助手"
            history_lines.append(f"{role_label}: {msg['content'][:100]}")
        return "\n".join(history_lines)
    
    async def _understand_query(self, question: str) -> tuple[List[str], str]:
        """
        Query understanding: entity recognition and query rewriting.
        Returns: (entities, rewritten_query)
        """
        # Simple entity extraction using regex patterns
        entities = []
        
        # Medical term patterns (简单实现，生产环境应使用 NER 模型)
        patterns = {
            r'(透析|血液透析|腹膜透析)': '透析',
            r'(糖尿病|2型糖尿病|二型糖尿病)': '糖尿病',
            r'(高血压|原发性高血压)': '高血压',
            r'(冠心病|冠状动脉粥样硬化性心脏病)': '冠心病',
            r'(CT|核磁|MRI|X光|超声)': '医学影像',
        }
        
        for pattern, standard_entity in patterns.items():
            if re.search(pattern, question, re.IGNORECASE):
                entities.append(standard_entity)
        
        # Query rewriting using LLM (optional, for now skip to save time)
        # In production, call LLM with prompt_builder.build_query_rewrite_prompt()
        rewritten_query = None  # Use original query for now
        
        return entities, rewritten_query
    
    async def _simplified_retrieval(self, query: str, top_k: int = 8) -> List[Dict]:
        """
        Simplified retrieval using only keyword and vector search (no graph search).
        This is faster than the full multi-channel approach.
        """
        try:
            # 使用 search_service 进行关键词 + 向量检索
            results = await self.search_service.search(
                query=query,
                top_k=top_k,
                search_type="hybrid"  # 混合搜索：关键词 + 向量
            )
            
            logger.info(f"Simplified retrieval returned {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Simplified retrieval failed: {e}, falling back to graph search")
            # 如果失败，降级到图谱搜索
            try:
                return await self.graph_db.search_policies(query, top_k=top_k)
            except Exception as e2:
                logger.error(f"Fallback graph search also failed: {e2}")
                return []
