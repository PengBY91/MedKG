from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
import logging

class QualityRule:
    """Definition of a data quality rule."""
    def __init__(
        self,
        id: str,
        name: str,
        condition: str,  # Pandas query string, e.g., "age > 0 and age < 120"
        description: str = "",
        severity: str = "warning", # error, warning, info
        category: str = "validity" # completeness, validity, consistency, accuracy
    ):
        self.id = id
        self.name = name
        self.condition = condition
        self.description = description
        self.severity = severity
        self.category = category

class QualityRuleEngine:
    """Engine to execute quality rules on datasets."""
    
    def __init__(self):
        self.rules: Dict[str, QualityRule] = {}
        self._setup_default_rules()

    def _setup_default_rules(self):
        """Add some basic medical data quality rules."""
        default_rules = [
            QualityRule(
                "QR-BP-01",
                "Blood Pressure Logic",
                "systolic_bp > diastolic_bp",
                "收缩压必须大于舒张压",
                "error"
            ),
            QualityRule(
                "QR-AGE-01",
                "Age Range Check",
                "age >= 0 and age <= 150",
                "年龄必须在0-150岁之间",
                "error"
            ),
            QualityRule(
                "QR-GENDER-DIAG",
                "Gender/Diagnosis Check",
                "not (gender == 'Male' and diagnosis == 'Uterine Fibroids')",
                "男性患者不能有子宫肌瘤诊断",
                "error"
            )
        ]
        for r in default_rules:
            self.rules[r.id] = r

    def add_rule(self, rule: QualityRule):
        self.rules[rule.id] = rule

    def validate_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate a dataframe against registered rules."""
        results = []
        total_records = len(df)
        
        if total_records == 0:
            return {"record_count": 0, "passed": True, "violations": []}

        summary = {
            "total_records": total_records,
            "passed_records": total_records,
            "failed_records": 0,
            "quality_score": 1.0,
            "violations_by_rule": {}
        }

        # Track indices of failed records
        overall_failed_indices = set()

        for rule_id, rule in self.rules.items():
            try:
                # Identify records that DO NOT satisfy the condition
                # Use query to find invalid records
                # Note: condition is what valid records should satisfy
                invalid_df = df.query(f"not ({rule.condition})", engine='python')
                
                fail_count = len(invalid_df)
                if fail_count > 0:
                    summary["violations_by_rule"][rule.id] = {
                        "name": rule.name,
                        "description": rule.description,
                        "count": fail_count,
                        "severity": rule.severity,
                        "sample_ids": invalid_df.index[:5].tolist()
                    }
                    overall_failed_indices.update(invalid_df.index.tolist())
            except Exception as e:
                logging.error(f"Error executing rule {rule.name}: {e}")
                continue

        failed_count = len(overall_failed_indices)
        summary["failed_records"] = failed_count
        summary["passed_records"] = total_records - failed_count
        summary["quality_score"] = (total_records - failed_count) / total_records if total_records > 0 else 1.0

        return summary

# Singleton
quality_engine = QualityRuleEngine()
