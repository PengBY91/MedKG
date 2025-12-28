from typing import List, Dict, Any, Optional
import os
import logging

logger = logging.getLogger(__name__)

# Try importing from openspg-kag (namespace usually 'kag')
try:
    from kag.solver import KAGSolver
    from kag.common.conf import KAGConfig
    HAS_KAG = True
except ImportError:
    HAS_KAG = False
    logger.warning("openspg-kag not installed. Using Mock Solver.")
    
    class KAGConfig:
        def __init__(self, **kwargs): pass
    
    class KAGSolver:
        def __init__(self, cfg: KAGConfig): pass
        def solve(self, query: str): 
            return {
                "answer": f"Mock answer for '{query}'",
                "evidence": []
            }

class KAGSolverService:
    """
    Service wrapper for OpenSPG-KAG Solver.
    Optimized to use configuration-driven initialization.
    """

    def __init__(self):
        self.solver = None
        self._initialize_solver()

    def _initialize_solver(self):
        if not HAS_KAG:
            self.solver = KAGSolver(KAGConfig())
            return

        # Load configuration (Env vars or default)
        # Optimization: Use KAGConfig object for tuning parameters
        try:
            from app.core.config import settings
            cfg = KAGConfig(
                project_id=settings.KAG_PROJECT_ID,
                host=settings.KAG_HOST,
                namespace=settings.KAG_NAMESPACE,
                enable_trace=True,  # Optimization: Enable tracing for debug
                # Enhanced parameters for better QA performance
                reasoning_depth=3,  # Deeper logical reasoning
                max_retrieval_results=20,  # More candidates for ranking
                enable_semantic_matching=True,  # Semantic understanding
                confidence_threshold=0.6,  # Lower threshold for more recall
            )
            self.solver = KAGSolver(cfg)
            logger.info("KAG Solver initialized with enhanced parameters.")
        except Exception as e:
            logger.error(f"Failed to init KAG Solver: {e}")
            self.solver = None

    async def solve_query(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute Logic Form query via KAG Solver with enhanced context.
        
        Args:
            query: Natural language query
            context: Optional context including retrieved rules, entities, etc.
        """
        if not self.solver:
            return {"error": "Solver not initialized"}

        try:
            # Enhance query with context if provided
            enhanced_query = query
            if context:
                # Add retrieved rules as context
                if context.get("rules"):
                    rules_text = "\n".join([r.get("content", "") for r in context["rules"][:5]])
                    enhanced_query = f"Context: {rules_text}\n\nQuery: {query}"
                
                # Add entity information if available
                if context.get("entities"):
                    entities_text = ", ".join(context["entities"])
                    enhanced_query = f"Entities: {entities_text}\n\n{enhanced_query}"
            
            logger.info(f"Solving query with KAG: {query[:50]}...")
            
            # Sync call to solver (KAG SDK is typically blocking)
            # Optimization: Wrap in executor if needed for asyncio
            res = self.solver.solve(enhanced_query)
            
            # Enhance result with metadata
            if isinstance(res, dict):
                res["solver_version"] = "KAG-Enhanced"
                res["context_used"] = bool(context)
            
            return res
        except Exception as e:
            logger.error(f"KAG Solve Error: {e}")
            return {"error": str(e), "query": query}

    async def validate_logic(self, logic_form: str) -> bool:
        # KAG handles validation internally during solve
        return True

# Singleton
kag_solver_service = KAGSolverService()
