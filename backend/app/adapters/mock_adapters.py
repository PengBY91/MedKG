import asyncio
import json
from typing import List, Dict, Any
from app.core.interfaces import LLMProvider, VectorStoreAdapter

class MockLLMProvider(LLMProvider):
    async def generate(self, prompt: str, schema: Dict[str, Any] = None) -> str:
        # Simulate latency
        await asyncio.sleep(0.5)
        
        if "answer the policy question" in prompt or "解释" in prompt:
             return "根据《基本医疗保险门诊特殊疾病管理规定（2024版）》，门诊血液透析每日治疗费用限额为420元。由于该患者当日透析费用为450元，超出限额的30元部分不予报销。"
             
        # 1. Rule Extraction Loophole
        if "Extract structured information from this rule" in prompt:
            # Rule Extraction for LimitParser
            if "透析" in prompt:
                return json.dumps({
                    "subject": "门诊透析",
                    "limit_value": 420,
                    "time_window": "daily"
                })
            return json.dumps({
                "subject": "Unknown",
                "limit_value": 0,
                "time_window": "null"
            })

        if "Classify this medical insurance policy rule" in prompt:
            if any(kw in prompt for kw in ["限额", "限制", "最多", "不超过", "平铺", "limit"]):
                return "limit"
            if any(kw in prompt for kw in ["不得同时", "互斥", "exclusion"]):
                return "exclusion"
            return "limit"

        # 3. Standard Terminology Matching (General)
        if "Standardize" in prompt or "standard medical code" in prompt:
           if "二型糖" in prompt: return '{"code": "E11.101", "reason": "匹配2型糖尿病伴有酮症酸中毒"}'
           if "高血压" in prompt: return '{"code": "I10.X00", "reason": "匹配原发性高血压标准编码"}'
           if "冠心病" in prompt: return '{"code": "I25.101", "reason": "匹配冠心病常用编码"}'

        return '{"code": "UNKNOWN", "reason": "未找到匹配项", "subject": "Unknown", "limit_value": 0}'

class MockVectorStoreAdapter(VectorStoreAdapter):
    def __init__(self):
        self.store = []

    async def search(self, query_text: str, top_k: int = 10) -> List[Dict[str, Any]]:
        await asyncio.sleep(0.1)
        # Return mock candidates based on query
        if "糖尿病" in query_text:
            return [
                {"text": "E11.101 - 2型糖尿病伴有酮症酸中毒", "score": 0.95, "metadata": {"code": "E11.101"}},
                {"text": "E11.900 - 2型糖尿病不伴有并发症", "score": 0.85, "metadata": {"code": "E11.900"}}
            ]
        elif "高血压" in query_text:
            return [
                {"text": "I10.X00 - 原发性高血压", "score": 0.98, "metadata": {"code": "I10.X00"}},
                {"text": "I15.900 - 继发性高血压", "score": 0.75, "metadata": {"code": "I15.900"}}
            ]
        return [
            {"text": "通用字典码 001", "score": 0.5, "metadata": {"code": "001"}},
        ]

    async def add_texts(self, texts: List[str], metadata: List[Dict[str, Any]]):
        self.store.extend(zip(texts, metadata))

