from abc import ABC, abstractmethod
from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class SHACLModel:
    """Intermediate representation of a rule before SHACL generation."""
    rule_type: str
    subject: str
    predicate: str
    object_value: Any
    severity: str = "Violation"

class RuleParserPlugin(ABC):
    @abstractmethod
    def can_handle(self, policy_type: str) -> bool:
        """Check if this plugin can handle the given policy type."""
        pass
    
    @abstractmethod
    async def parse(self, text: str, llm) -> SHACLModel:
        """Parse natural language into intermediate representation."""
        pass
