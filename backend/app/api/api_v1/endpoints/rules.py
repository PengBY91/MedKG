from fastapi import APIRouter, Body
from app.services.rule_service import RuleCompiler
from app.services.sandbox_service import SandboxRunner
from app.adapters.mock_adapters import MockLLMProvider
from app.adapters.neo4j_adapter import Neo4jAdapter

from app.services.knowledge_store_service import knowledge_store

router = APIRouter()

# Dependency Injection
llm = MockLLMProvider()
graph_db = Neo4jAdapter()
rule_compiler = RuleCompiler(llm)
sandbox_runner = SandboxRunner(graph_db)

@router.get("/")
async def list_rules():
    """List all persisted rules."""
    return knowledge_store.get_all_rules()

@router.post("/")
async def add_rule(rule_data: dict = Body(...)):
    """Add a rule manually or from compilation result."""
    return knowledge_store.add_rule(rule_data)

@router.delete("/{rule_id}")
async def delete_rule(rule_id: str):
    """Delete a rule by ID."""
    knowledge_store.delete_rule(rule_id)
    return {"status": "success"}

@router.post("/compile")
async def compile_rule(policy_text: str = Body(..., embed=True)):
    """
    Compile natural language policy into SHACL rules using LLM.
    """
    return await rule_compiler.compile(policy_text)

@router.post("/test")
async def test_rule(
    shacl_content: str = Body(...),
    test_dataset: str = Body("last_month_patients")
):
    """
    Test a SHACL rule in sandbox environment against historical data.
    Returns validation report with rejection rate metrics.
    """
    return await sandbox_runner.run_test(shacl_content, test_dataset)



