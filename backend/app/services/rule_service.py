from typing import List, Dict, Any
import logging
from kag.interface.common.llm_client import LLMClient
from kag.common.conf import KAG_CONFIG
from app.core.config import settings

logger = logging.getLogger(__name__)

class RuleCompiler:
    """
    Rule Compiler using real KAG LLM for rule generation and validation.
    """
    
    def __init__(self):
        """Initialize with real KAG LLM client."""
        try:
            if not KAG_CONFIG._is_initialized:
                import os
                config_path = os.path.join(settings.PROJECT_ROOT, "config/kag_config.yaml")
                KAG_CONFIG.initialize(prod=False, config_file=config_path)
            
            llm_config = KAG_CONFIG.all_config.get("chat_llm")
            if not llm_config:
                raise ValueError("chat_llm not found in config/kag_config.yaml")
            
            self.llm = LLMClient.from_config(llm_config)
            logger.info("RuleCompiler initialized with real LLM")
        except Exception as e:
            logger.error(f"Failed to initialize RuleCompiler: {e}")
            raise RuntimeError(f"LLM initialization failed: {e}")
    
    async def compile_rule(self, rule_text: str) -> Dict[str, Any]:
        """Compile natural language rule to executable format using LLM."""
        try:
            prompt = f"""将以下自然语言规则转换为可执行的规则格式:

规则: {rule_text}

请以JSON格式返回,包含:
- condition: 条件表达式
- action: 执行动作
- priority: 优先级(1-10)
"""
            response = self.llm(prompt)
            import json
            rule_def = json.loads(response)
            return {"status": "success", "rule": rule_def}
        except Exception as e:
            logger.error(f"Rule compilation failed: {e}")
            return {"status": "error", "message": str(e)}
    
    async def validate_rule(self, rule_def: Dict[str, Any]) -> bool:
        """Validate rule using LLM."""
        try:
            prompt = f"""验证以下规则是否合法和合理:

{rule_def}

请返回 "valid" 或 "invalid" 以及原因。
"""
            response = self.llm(prompt)
            return "valid" in response.lower()
        except Exception as e:
            logger.error(f"Rule validation failed: {e}")
            return False

# Singleton instance
rule_service = RuleCompiler()
