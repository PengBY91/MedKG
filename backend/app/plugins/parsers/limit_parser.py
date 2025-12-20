import json
from app.plugins.rule_parser_plugin import RuleParserPlugin, SHACLModel

class LimitRuleParser(RuleParserPlugin):
    def can_handle(self, policy_type: str) -> bool:
        keywords = ["限额", "限制", "不超过", "最多", "limit", "cap"]
        return any(kw in policy_type for kw in keywords)
    
    async def parse(self, text: str, llm) -> SHACLModel:
        prompt = f"""
        You are a medical policy analyst. Extract structured information from this rule:
        
        Rule: "{text}"
        
        Extract:
        1. Subject: What entity is being limited? (e.g., "门诊透析", "住院费用")
        2. Limit Value: The numeric threshold (e.g., 400, 5000)
        3. Time Window: If applicable (e.g., "每日", "每月")
        
        Output JSON:
        {{
            "subject": "extracted_subject",
            "limit_value": numeric_value,
            "time_window": "daily|monthly|per_visit|null"
        }}
        """
        
        response = await llm.generate(prompt)
        try:
            parsed = json.loads(response)
            return SHACLModel(
                rule_type="LimitRule",
                subject=parsed.get("subject", "Unknown"),
                predicate="hasMaxCost",
                object_value=parsed.get("limit_value", 0),
                severity="Violation"
            )
        except Exception as e:
            print(f"Parse error: {e}")
            return SHACLModel(
                rule_type="LimitRule",
                subject="Unknown",
                predicate="hasMaxCost",
                object_value=0
            )
