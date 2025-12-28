from typing import List, Dict, Any

class PromptBuilder:
    """
    Constructs Few-Shot Prompts for DeepKE/LLM extraction.
    Implements:
    1. Schema Injection: Including entity/relation definitions.
    2. Support Set Injection: Including 3-5 labeled examples.
    3. Policy QA Prompt: Structured prompts for policy question answering.
    """

    def __init__(self, schema_svc=None):
        self.schema = schema_svc

    def build_ner_prompt(self, text: str, examples: List[Dict[str, Any]] = None) -> str:
        """
        Build prompt for Entity Extraction.
        """
        schema_info = "Entities to extract: [Disease, Drug, Symptom, Surgery]"
        
        prompt = f"""
        You are a medical data extraction assistant.
        {schema_info}
        
        Examples:
        """
        
        # In-Context Learning Support Set
        if examples:
            for ex in examples:
                prompt += f"\nText: {ex['text']}\nEntities: {ex['entities']}\n"
        
        prompt += f"\nNow extract from the following text:\nText: {text}\nEntities:"
        return prompt

    def build_re_prompt(self, text: str, entities: List[Dict], examples: List[Dict] = None) -> str:
        """
        Build prompt for Relation Extraction.
        """
        relations = "[Treats, Contraindicates, Causes, Is_A]"
        
        prompt = f"""
        Identify relationships between the provided entities.
        Allowed Relations: {relations}
        
        Input Text: {text}
        Index Entities: {entities}
        """
        
        if examples:
            prompt += "\nExamples:"
            for ex in examples:
                 prompt += f"\nText: {ex['text']}\nRelations: {ex['relations']}"

        prompt += "\nReturns JSON list of relations:"
        return prompt
    
    def build_policy_qa_prompt(
        self, 
        question: str, 
        retrieved_rules: List[Dict[str, Any]] = None,
        kag_answer: str = None,
        entities: List[str] = None,
        standard_terms: Dict[str, str] = None
    ) -> str:
        """
        Build structured prompt for policy question answering.
        
        Args:
            question: User's question
            retrieved_rules: List of retrieved policy rules
            kag_answer: Answer from KAG solver
            entities: Identified medical entities in the question
            standard_terms: Standardized terminology mappings
        """
        
        # Build context section
        context_parts = []
        
        # 1. Retrieved Rules Context
        if retrieved_rules:
            rules_text = "【政策知识图谱检索结果】\n"
            for idx, rule in enumerate(retrieved_rules[:5], 1):
                rules_text += f"{idx}. 规则: {rule.get('name', '未知规则')}\n"
                rules_text += f"   来源: {rule.get('parent_doc', '规则库')}\n"
                rules_text += f"   内容: {rule.get('content', '无详细内容')}\n"
                if rule.get('score'):
                    rules_text += f"   相关度: {rule['score']:.2f}\n"
                rules_text += "\n"
            context_parts.append(rules_text)
        else:
            context_parts.append("【政策知识图谱检索结果】\n暂无直接相关的结构化政策条目。\n")
        
        # 2. KAG Logic Reasoning
        if kag_answer:
            kag_text = f"【KAG 逻辑推理结论】\n{kag_answer}\n"
            context_parts.append(kag_text)
        
        # 3. Entity Information
        if entities:
            entity_text = f"【识别的医学实体】\n{', '.join(entities)}\n"
            context_parts.append(entity_text)
        
        # 4. Standard Terminology
        if standard_terms:
            std_text = "【术语标准化映射】\n"
            for original, standard in standard_terms.items():
                std_text += f"- {original} → {standard}\n"
            context_parts.append(std_text)
        
        # Build full prompt
        full_context = "\n".join(context_parts)
        
        prompt = f"""你是一位专业的智能医保政策助手。请基于以下多源知识进行综合推理，回答用户问题。

{full_context}

【用户问题】
{question}

【回答要求】
1. **证据引用**: 若图谱或 KAG 中有明确依据，请在回答开头标注【图谱协同结论】，并准确引用条目名称和来源。
2. **术语标准化**: 若涉及医学检查或疾病名称，请优先使用标准化术语，并说明标准名称。
3. **多源融合**: 综合图谱检索、KAG 逻辑推理和领域知识，形成完整准确的回答。
4. **置信度说明**: 若信息不足或不确定，请在回答开头标注【泛知识参考】，并说明推理依据。
5. **政策严谨性**: 必须体现政策的严谨性，最后附带免责声明："以上回答基于当前政策库（截至检索时间），具体执行请以官方最新发文为准。"
6. **结构化输出**: 使用分点论述，条理清晰。

【回答】
"""
        return prompt
    
    def build_query_rewrite_prompt(self, question: str, entities: List[str] = None) -> str:
        """
        Build prompt for query understanding and rewriting.
        """
        entity_context = f"已识别实体: {', '.join(entities)}" if entities else ""
        
        prompt = f"""你是一位查询理解专家。请分析用户问题，提取关键信息并改写为更精确的查询语句。

{entity_context}

【用户原始问题】
{question}

【分析任务】
1. 识别查询意图（政策咨询、费用查询、资格判断等）
2. 提取核心医学实体（疾病、检查、药品等）
3. 识别查询约束条件（时间、地域、人群等）
4. 生成优化的查询语句（更适合知识图谱检索）

【输出格式（JSON）】
{{
  "intent": "查询意图",
  "entities": ["实体1", "实体2"],
  "constraints": {{"约束类型": "约束值"}},
  "rewritten_query": "优化后的查询语句"
}}
"""
        return prompt

# Singleton or factory
prompt_builder = PromptBuilder()
