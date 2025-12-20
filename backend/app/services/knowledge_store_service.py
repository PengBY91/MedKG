import json
import os
from typing import List, Dict, Any
import uuid

class KnowledgeStoreService:
    def __init__(self):
        self.rules_file = "data/knowledge_rules.json"
        self.terms_file = "data/knowledge_terms.json"
        self._check_dirs()
        self.rules = self._load(self.rules_file)
        self.terms = self._load(self.terms_file)

    def _check_dirs(self):
        os.makedirs("backend/data", exist_ok=True)

    def _load(self, path: str):
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    return json.load(f)
            except:
                return []
        return []

    def _save(self, path: str, data: list):
        with open(path, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    # --- Rules Management ---
    def get_all_rules(self) -> List[Dict]:
        return self.rules

    def add_rule(self, rule_data: Dict):
        if "id" not in rule_data:
            rule_data["id"] = str(uuid.uuid4())[:8]
        # Avoid duplicates
        self.rules = [r for r in self.rules if r.get("id") != rule_data["id"]]
        self.rules.append(rule_data)
        self._save(self.rules_file, self.rules)
        return rule_data

    def delete_rule(self, rule_id: str):
        self.rules = [r for r in self.rules if r.get("id") != rule_id]
        self._save(self.rules_file, self.rules)

    # --- Terminology Management ---
    def get_all_terms(self) -> List[Dict]:
        return self.terms

    def add_terms(self, terms_data: List[Dict]):
        # data format example: [{"term": "xxx", "code": "yyy"}]
        for item in terms_data:
            self.terms = [t for t in self.terms if t.get("term") != item["term"]]
            self.terms.append(item)
        self._save(self.terms_file, self.terms)
        return self.terms

    def delete_term(self, term: str):
        self.terms = [t for t in self.terms if t.get("term") != term]
        self._save(self.terms_file, self.terms)

# Singleton
knowledge_store = KnowledgeStoreService()
