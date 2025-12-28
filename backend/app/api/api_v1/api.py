from fastapi import APIRouter
from app.api.api_v1.endpoints import ingest, terminology, rules, explanation, auth, users, tenants, workflows, governance, policies, examination, system, graph, conversations

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(tenants.router, prefix="/tenants", tags=["tenants"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(workflows.router, prefix="/workflows", tags=["workflows"])
api_router.include_router(governance.router, prefix="/governance", tags=["data-governance"])
api_router.include_router(policies.router, prefix="/policies", tags=["policies"])
api_router.include_router(ingest.router, prefix="/ingest", tags=["ingest"])
api_router.include_router(terminology.router, prefix="/terminology", tags=["terminology"])
api_router.include_router(rules.router, prefix="/rules", tags=["rules"])
api_router.include_router(explanation.router, prefix="/explanation", tags=["explanation"])
api_router.include_router(conversations.router, prefix="/conversations", tags=["conversations"])
api_router.include_router(examination.router, prefix="/examination", tags=["examination"])
api_router.include_router(system.router, prefix="/system", tags=["system-config"])
api_router.include_router(graph.router, prefix="/graph", tags=["graph-explorer"])







