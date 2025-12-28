from typing import Dict, Any
from app.core.interfaces import LLMProvider
from app.adapters.neo4j_adapter import Neo4jAdapter
from app.services.kag_solver_service import kag_solver_service
import json
import logging

logger = logging.getLogger(__name__)

class ExplanationService:
    def __init__(self, graph_db: Neo4jAdapter, llm: LLMProvider):
        self.graph_db = graph_db
        self.llm = llm
    
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
        Answer policy-related questions using GraphRAG and OpenSPG-KAG.
        """
        logger.info(f"Querying policy with KAG and GraphRAG for: {question}")
        
        # 1. Retrieval Phase: Search graph for relevant rules/policies (Traditional GraphRAG)
        related_nodes = await self.graph_db.search_policies(question)
        
        context_str = ""
        if related_nodes:
            context_str = "\n".join([
                f"- 规则: {n['name']} ({n['reference']})\n  所属文件: {n['parent_doc']}\n  规则内容: {n['content']}"
                for n in related_nodes
            ])
        
        # 2. OpenSPG-KAG Phase: Solve via Logic Form / DSL
        kag_result = await kag_solver_service.solve_query(question)
        kag_answer = kag_result.get("answer") if "error" not in kag_result else None
        
        # 3. Reasoning Fusion Phase: Grounded LLM generation
        # Inject KAG results into prompt if available to strengthen the answer
        kag_context = f"\n[KAG 逻辑推理建议]:\n{kag_answer}\n" if kag_answer else ""
        
        prompt = f"""
你是一位智能医保助手。请基于「政策知识图谱」检索到的条目和「KAG 逻辑推理结论」，结合大模型的推理能力回答问题。

[图谱检索结果]:
{context_str if context_str else "知识图谱中暂无直接相关的结构化政策条目。"}
{kag_context}

[用户问题]: "{question}"

要求:
1. 若图谱或 KAG 中有明确依据，请在回答开头标注【图谱协同结论】，并准确引用条目名称。
2. 若涉及医学检查名称，请优先查看是否存在【标准化术语】(StdTerm)，并指出标准名称。
3. 若信息不足，请在回答开头标注【泛知识参考】，结合医学知识库进行合理解释。
3. 必须体现出政策的严谨性，最后附带提示：“以上回答基于当前政策库，具体执行请以官方发文为准”。

输出方案：
"""
        answer = await self.llm.generate(prompt)
        
        # Collaborative Reasoning Trace for Backend transparency
        reasoning_path = [
            {"step": "1. Graph Index Lookup", "status": "Done", "detail": f"检索关键词: {question[:10]}..."},
            {"step": "2. OpenSPG-KAG Logic Solving", "status": "Success" if kag_answer else "Skipped", 
             "detail": "KAG 成功生成逻辑查询并执行" if kag_answer else "KAG 暂无直接匹配逻辑口径，切回通用语义模式"},
            {"step": "3. Knowledge Fusion reasoning", "status": "Done", "detail": "多源知识注入 LLM Prompt 进行融合生成"}
        ]
        
        return {
            "question": question,
            "answer": answer,
            "sources": related_nodes,
            "reasoning_trace": reasoning_path,
            "kag_raw": kag_result
        }
