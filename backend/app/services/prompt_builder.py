from typing import List, Dict, Any

class PromptBuilder:
    """
    Constructs Few-Shot Prompts for DeepKE/LLM extraction.
    Implements:
    1. Schema Injection: Including entity/relation definitions.
    2. Support Set Injection: Including 3-5 labeled examples.
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

# Singleton or factory
prompt_builder = PromptBuilder()
