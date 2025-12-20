from typing import List, Dict, Any
from app.core.interfaces import LLMProvider
from app.plugins.rule_parser_plugin import RuleParserPlugin, SHACLModel
from app.plugins.parsers.limit_parser import LimitRuleParser
import re
import uuid

class RuleCompiler:
    def __init__(self, llm: LLMProvider):
        self.llm = llm
        self.plugins: List[RuleParserPlugin] = [
            LimitRuleParser(),
            # Add more parsers here
        ]
    
    async def compile(self, policy_text: str, max_retries: int = 3) -> Dict[str, Any]:
        """
        Compile natural language policy into SHACL.
        Includes self-correction loop.
        """
        # Step 1: Classify rule type
        rule_type = await self._classify_rule_type(policy_text)
        
        # Step 2: Find appropriate plugin
        parser = self._find_parser(rule_type)
        if not parser:
            return {
                "status": "error",
                "message": f"No parser found for rule type: {rule_type}"
            }
        
        # Step 3: Parse to intermediate representation
        ir_model = await parser.parse(policy_text, self.llm)
        
        # Step 4: Generate SHACL
        shacl_code = self._generate_shacl(ir_model)
        
        # Step 5: Validate with self-correction
        for attempt in range(max_retries):
            is_valid, error = self._validate_shacl(shacl_code)
            if is_valid:
                return {
                    "status": "success",
                    "shacl_content": shacl_code,
                    "rule_type": rule_type,
                    "subject": ir_model.subject,
                    "object_value": ir_model.object_value,
                    "explanation": f"Rule compiled successfully as {ir_model.rule_type}"
                }
            else:
                # Self-correction
                shacl_code = await self._self_correct(shacl_code, error)
        
        return {
            "status": "error",
            "message": "Failed to generate valid SHACL after retries",
            "last_attempt": shacl_code
        }
    
    async def _classify_rule_type(self, text: str) -> str:
        """Use LLM to classify rule type."""
        prompt = f"""
        Classify this medical insurance policy rule into one category:
        - "limit" (for cost/frequency limits)
        - "exclusion" (for mutually exclusive treatments)
        - "mandatory" (for required procedures)
        
        Rule: "{text}"
        
        Output only the category name.
        """
        response = await self.llm.generate(prompt)
        return response.strip().lower()
    
    def _find_parser(self, rule_type: str) -> RuleParserPlugin:
        """Find the first plugin that can handle this rule type."""
        for plugin in self.plugins:
            if plugin.can_handle(rule_type):
                return plugin
        return None
    
    def _generate_shacl(self, model: SHACLModel) -> str:
        # Load template
        import os
        template_path = os.path.join(os.path.dirname(__file__), "..", "templates", "limit_rule.ttl")
        with open(template_path, "r") as f:
            template = f.read()
        
        # Simple string replacement
        shacl = template.replace("{{rule_id}}", str(uuid.uuid4())[:8])
        shacl = shacl.replace("{{target_class}}", self._to_class_name(model.subject))
        shacl = shacl.replace("{{predicate}}", model.predicate)
        shacl = shacl.replace("{{limit_value}}", str(model.object_value))
        shacl = shacl.replace("{{severity}}", model.severity)
        shacl = shacl.replace("{{subject}}", model.subject)
        
        return shacl
    
    def _to_class_name(self, subject: str) -> str:
        """Convert Chinese subject to class name."""
        # Simplified mapping
        mapping = {
            "门诊透析": "OutpatientDialysis",
            "住院": "InpatientVisit",
        }
        return mapping.get(subject, "MedicalService")
    
    def _validate_shacl(self, shacl_code: str) -> tuple[bool, str]:
        """
        Validate SHACL syntax.
        In production, use pyshacl library.
        """
        # Simple syntax check
        required_keywords = ["sh:NodeShape", "sh:targetClass", "sh:property"]
        for kw in required_keywords:
            if kw not in shacl_code:
                return False, f"Missing required keyword: {kw}"
        
        # Check for balanced brackets
        if shacl_code.count('[') != shacl_code.count(']'):
            return False, "Unbalanced brackets"
        
        return True, ""
    
    async def _self_correct(self, shacl_code: str, error: str) -> str:
        """Ask LLM to fix the SHACL code."""
        prompt = f"""
        The following SHACL code has an error:
        
        Error: {error}
        
        Code:
        {shacl_code}
        
        Please fix the error and output the corrected SHACL code.
        """
        corrected = await self.llm.generate(prompt)
        return corrected

from app.adapters.mock_adapters import MockLLMProvider
rule_service = RuleCompiler(MockLLMProvider())
