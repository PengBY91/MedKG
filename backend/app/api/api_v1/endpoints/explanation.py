from fastapi import APIRouter, Query
from app.services.explanation_service import ExplanationService
from app.adapters.neo4j_adapter import Neo4jAdapter
from app.adapters.mock_adapters import MockLLMProvider

router = APIRouter()

# Dependency Injection
graph_db = Neo4jAdapter()
llm = MockLLMProvider()
explanation_service = ExplanationService(graph_db, llm)


@router.post("/query")
async def query_policy(question: str):
    """
    Answer policy-related questions using knowledge graph.
    """
    instruction = f"[CONTEXT: answer the policy question] {question}"
    return await explanation_service.query_policy(instruction)
