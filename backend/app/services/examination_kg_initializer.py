"""
Examination Knowledge Graph Initializer
Initializes the ontology for medical examination standardization.
"""

from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

# Examination Ontology Data
EXAMINATION_ONTOLOGY = {
    "body_parts_level1": [
        "头颈部",
        "胸部", 
        "腹部",
        "上肢",
        "下肢",
        "脊柱",
        "骨盆"
    ],
    
    "body_parts_level2": {
        "头颈部": ["颅骨", "鼻骨", "颧骨", "下颌骨", "颈椎", "甲状腺", "颈部软组织"],
        "胸部": ["胸廓", "肋骨", "胸椎", "胸骨", "锁骨", "肺", "纵隔", "心脏"],
        "腹部": ["腹腔", "肝脏", "胆囊", "胰腺", "脾脏", "肾脏", "胃", "肠道"],
        "上肢": ["手指", "手掌", "腕关节", "前臂", "桡骨", "尺骨", "肘关节", "上臂", "肱骨", "肩关节", "锁骨"],
        "下肢": ["足趾", "足部", "跟骨", "踝关节", "小腿", "胫骨", "腓骨", "膝关节", "髌骨", "大腿", "股骨", "髋关节"],
        "脊柱": ["颈椎", "胸椎", "腰椎", "骶椎", "尾椎", "全脊柱"],
        "骨盆": ["骨盆", "髋臼", "耻骨", "坐骨", "骶髂关节"]
    },
    
    "examination_methods": [
        "正位",
        "侧位",
        "斜位",
        "轴位",
        "切线位",
        "前后位",
        "后前位",
        "开口位",
        "过伸位",
        "过屈位",
        "内旋位",
        "外旋位",
        "站立位",
        "卧位",
        "负重位"
    ],
    
    "modalities": [
        "DR",  # Digital Radiography
        "CT",  # Computed Tomography
        "MRI", # Magnetic Resonance Imaging
        "US",  # Ultrasound
        "DSA", # Digital Subtraction Angiography
        "PET", # Positron Emission Tomography
        "ECT", # Emission Computed Tomography
        "CR",  # Computed Radiography
        "DXA"  # Dual-energy X-ray Absorptiometry
    ],
    
    # Common aliases and variations
    "aliases": {
        "正侧位": ["正位", "侧位"],
        "正斜位": ["正位", "斜位"],
        "双斜位": ["斜位"],
        "AP": "前后位",
        "PA": "后前位",
        "LAT": "侧位",
        "OBL": "斜位"
    }
}


class ExaminationKGInitializer:
    """
    Initializer for Examination Knowledge Graph.
    Provides methods to load ontology data and validate examination triples.
    """
    
    def __init__(self):
        self.ontology = EXAMINATION_ONTOLOGY
        logger.info("Examination KG Initializer loaded with ontology data")
    
    def get_level1_parts(self) -> List[str]:
        """Get all level 1 body parts."""
        return self.ontology["body_parts_level1"]
    
    def get_level2_parts(self, level1: str = None) -> List[str]:
        """Get level 2 body parts, optionally filtered by level 1."""
        if level1:
            return self.ontology["body_parts_level2"].get(level1, [])
        # Return all level 2 parts
        all_parts = []
        for parts in self.ontology["body_parts_level2"].values():
            all_parts.extend(parts)
        return list(set(all_parts))
    
    def get_methods(self) -> List[str]:
        """Get all examination methods."""
        return self.ontology["examination_methods"]
    
    def get_modalities(self) -> List[str]:
        """Get all examination modalities."""
        return self.ontology["modalities"]
    
    def get_aliases(self) -> Dict[str, Any]:
        """Get method aliases."""
        return self.ontology["aliases"]
    
    def validate_triple(self, level1: str, level2: str, method: str) -> bool:
        """
        Validate if a triple [level1, level2, method] is valid according to ontology.
        
        Args:
            level1: Level 1 body part
            level2: Level 2 body part
            method: Examination method
            
        Returns:
            True if valid, False otherwise
        """
        # Check level 1
        if level1 not in self.ontology["body_parts_level1"]:
            logger.warning(f"Invalid level1 part: {level1}")
            return False
        
        # Check level 2 belongs to level 1
        level2_parts = self.ontology["body_parts_level2"].get(level1, [])
        if level2 not in level2_parts:
            logger.warning(f"Invalid level2 part '{level2}' for level1 '{level1}'")
            return False
        
        # Check method
        if method not in self.ontology["examination_methods"]:
            logger.warning(f"Invalid examination method: {method}")
            return False
        
        return True
    
    def find_level1_for_level2(self, level2: str) -> str:
        """
        Find the level 1 body part that contains the given level 2 part.
        
        Args:
            level2: Level 2 body part
            
        Returns:
            Level 1 body part or None if not found
        """
        for level1, parts in self.ontology["body_parts_level2"].items():
            if level2 in parts:
                return level1
        return None
    
    def expand_method_alias(self, method_text: str) -> List[str]:
        """
        Expand method aliases (e.g., "正侧位" -> ["正位", "侧位"]).
        
        Args:
            method_text: Method text that might be an alias
            
        Returns:
            List of expanded methods
        """
        if method_text in self.ontology["aliases"]:
            alias_value = self.ontology["aliases"][method_text]
            if isinstance(alias_value, list):
                return alias_value
            else:
                return [alias_value]
        return [method_text]
    
    def get_ontology_summary(self) -> Dict[str, Any]:
        """Get a summary of the ontology for display purposes."""
        return {
            "level1_count": len(self.ontology["body_parts_level1"]),
            "level2_count": sum(len(parts) for parts in self.ontology["body_parts_level2"].values()),
            "methods_count": len(self.ontology["examination_methods"]),
            "modalities_count": len(self.ontology["modalities"]),
            "level1_parts": self.ontology["body_parts_level1"],
            "methods": self.ontology["examination_methods"],
            "modalities": self.ontology["modalities"]
        }


# Singleton instance
examination_kg = ExaminationKGInitializer()
