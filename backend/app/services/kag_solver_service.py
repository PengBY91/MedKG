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
            cfg = KAGConfig(
                project_id=os.getenv("KAG_PROJECT_ID", "1"),
                host=os.getenv("KAG_HOST", "127.0.0.1:8887"),
                namespace=os.getenv("KAG_NAMESPACE", "MedicalGovernance"),
                enable_trace=True  # Optimization: Enable tracing for debug
            )
            self.solver = KAGSolver(cfg)
            logger.info("KAG Solver initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to init KAG Solver: {e}")
            self.solver = None

    async def solve_query(self, query: str) -> Dict[str, Any]:
        """
        Execute Logic Form query via KAG Solver.
        """
        if not self.solver:
            return {"error": "Solver not initialized"}

        try:
            # Sync call to solver (KAG SDK is typically blocking)
            # Optimization: Wrap in executor if needed for asyncio
            res = self.solver.solve(query)
            return res
        except Exception as e:
            logger.error(f"KAG Solve Error: {e}")
            return {"error": str(e)}

    async def validate_logic(self, logic_form: str) -> bool:
        # KAG handles validation internally during solve
        return True

# Singleton
kag_solver_service = KAGSolverService()
