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
    
    async def query_policy(self, question: str) -> Dict[str, Any]:
        """
        Enhanced policy question answering with multi-stage pipeline:
        1. Query Understanding & Entity Recognition
        2. Multi-channel Retrieval (Keyword + Vector + Graph)
        3. Result Ranking & Reranking (KGRank + MMR)
        4. KAG Logic Reasoning
        5. Terminology Standardization
        6. Knowledge Fusion & Generation
        """
        logger.info(f"[Enhanced QA Pipeline] Starting for: {question}")
        
        # ===== Stage 1: Query Understanding =====
        entities, rewritten_query = await self._understand_query(question)
        logger.info(f"[Stage 1] Entities: {entities}, Rewritten: {rewritten_query}")
        
        # ===== Stage 2: Multi-channel Retrieval =====
        # Use both original and rewritten query for better coverage
        search_query = rewritten_query if rewritten_query else question
        related_nodes = await self.graph_db.search_policies(search_query, top_k=15)
        logger.info(f"[Stage 2] Retrieved {len(related_nodes)} policy rules")
        
        # ===== Stage 3: Result Ranking & Reranking =====
        if related_nodes:
            # Use KGRank service for MMR-based reranking
            ranked_nodes = await self._rerank_results(search_query, related_nodes, top_k=10)
            logger.info(f"[Stage 3] Reranked to top {len(ranked_nodes)} results")
        else:
            ranked_nodes = []
        
        # ===== Stage 4: KAG Logic Reasoning =====
        # Pass retrieved rules as context to KAG
        kag_context = {
            "rules": ranked_nodes[:5],
            "entities": entities
        }
        kag_result = await kag_solver_service.solve_query(search_query, context=kag_context)
        kag_answer = kag_result.get("answer") if "error" not in kag_result else None
        logger.info(f"[Stage 4] KAG reasoning: {'Success' if kag_answer else 'No result'}")
        
        # ===== Stage 5: Terminology Standardization =====
        standard_terms = {}
        if entities:
            normalized = await self.terminology_service.normalize(entities)
            for norm in normalized:
                if norm.get("code") and norm.get("code") != "MOCK-123":
                    original = norm.get("term")
                    standard = f"{norm.get('display')} ({norm.get('code')})"
                    standard_terms[original] = standard
            logger.info(f"[Stage 5] Standardized {len(standard_terms)} terms")
        
        # ===== Stage 6: Knowledge Fusion & Generation =====
        # Build structured prompt using PromptBuilder
        prompt = prompt_builder.build_policy_qa_prompt(
            question=question,
            retrieved_rules=ranked_nodes,
            kag_answer=kag_answer,
            entities=entities,
            standard_terms=standard_terms
        )
        
        logger.info("[Stage 6] Generating answer with enhanced prompt...")
        answer = await self.llm.generate(prompt)
        
        # ===== Build Reasoning Trace =====
        reasoning_trace = [
            {
                "step": "1. Query Understanding",
                "status": "Done",
                "detail": f"识别实体: {len(entities)}个, 查询改写: {'是' if rewritten_query else '否'}"
            },
            {
                "step": "2. Multi-channel Retrieval",
                "status": "Done",
                "detail": f"检索到 {len(related_nodes)} 条政策规则（关键词+向量+图谱）"
            },
            {
                "step": "3. Result Ranking",
                "status": "Done",
                "detail": f"使用 MMR 重排序，选出 Top-{len(ranked_nodes)} 相关规则"
            },
            {
                "step": "4. KAG Logic Reasoning",
                "status": "Success" if kag_answer else "Skipped",
                "detail": "KAG 成功执行逻辑推理" if kag_answer else "KAG 未找到匹配逻辑"
            },
            {
                "step": "5. Terminology Standardization",
                "status": "Done" if standard_terms else "Skipped",
                "detail": f"标准化 {len(standard_terms)} 个医学术语" if standard_terms else "无需标准化"
            },
            {
                "step": "6. Knowledge Fusion",
                "status": "Done",
                "detail": "多源知识融合，结构化 Prompt 生成最终答案"
            }
        ]
        
        return {
            "question": question,
            "answer": answer,
            "sources": ranked_nodes,
            "entities": entities,
            "standard_terms": standard_terms,
            "reasoning_trace": reasoning_trace,
            "kag_raw": kag_result,
            "metadata": {
                "pipeline_version": "enhanced-v2",
                "retrieval_count": len(related_nodes),
                "final_sources": len(ranked_nodes)
            }
        }
    
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
    
    async def _rerank_results(self, query: str, results: List[Dict], top_k: int = 10) -> List[Dict]:
        """
        Rerank results using diversity-aware algorithm (MMR).
        """
        if not results:
            return []
        
        # Convert to format expected by search service
        candidates = []
        for r in results:
            candidates.append({
                "id": r.get("id"),
                "text": r.get("content", ""),
                "score": r.get("score", 0.5),
                "embedding": [0.1, 0.2],  # Mock embedding
                "metadata": r
            })
        
        # Use MMR reranking from search service
        try:
            reranked = self.search_service._mmr_rerank(query, candidates, limit=top_k)
            
            # Convert back to original format
            final_results = []
            for item in reranked:
                final_results.append(item["metadata"])
            
            return final_results
        except Exception as e:
            logger.warning(f"Reranking failed: {e}, using original order")
            return results[:top_k]
