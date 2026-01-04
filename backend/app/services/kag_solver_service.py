# backend/app/services/kag_solver_service.py
import os
import logging
from typing import Dict, Any, Optional
from kag.solver.main_solver import SolverMain
from kag.common.conf import KAG_CONFIG
from app.core.config import settings

logger = logging.getLogger(__name__)

class KAGSolverService:
    """
    KAG Solver Service for Medical Q&A
    Uses KAG's reasoning pipeline for multi-hop question answering
    """
    
    def __init__(self):
        self.config_path = os.path.join(settings.PROJECT_ROOT, "config/kag_config.yaml")
        self.solver = None
        
        try:
            # Initialize KAG config if not already done
            if not KAG_CONFIG._is_initialized:
                KAG_CONFIG.initialize(prod=False, config_file=self.config_path)
            
            # Initialize Solver Main (no arguments needed)
            self.solver = SolverMain()
            logger.info("KAGSolverService initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize KAGSolverService: {e}")
            self.solver = None
    
    async def solve_query(
        self, 
        query: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Solve a medical query using KAG reasoning pipeline
        
        Args:
            query: User's question in natural language
            context: Optional context (e.g., patient info, constraints)
        
        Returns:
            Dict containing:
            - answer: Generated answer
            - reasoning_trace: Step-by-step reasoning process
            - sources: Referenced knowledge nodes and chunks
        """
        if not self.solver:
            return {
                "status": "error",
                "message": "Solver not initialized. Check configuration.",
                "answer": None
            }
        
        try:
            logger.info(f"Solving query: {query}")
            
            # Use invoke method with required parameters
            result = self.solver.invoke(
                project_id=int(settings.KAG_PROJECT_ID),
                task_id="default_task",
                query=query,
                session_id="0",
                is_report=False,
                host_addr=settings.KAG_HOST,
                params=context or {}
            )
            
            # Extract answer and metadata
            if isinstance(result, dict):
                answer = result.get("answer", "")
                reasoning_trace = result.get("trace", [])
                sources = result.get("sources", [])
            else:
                answer = str(result) if result else "No answer generated"
                reasoning_trace = []
                sources = []
            
            logger.info(f"Query solved successfully. Answer length: {len(answer)}")
            
            return {
                "status": "success",
                "answer": answer,
                "reasoning_trace": reasoning_trace,
                "sources": sources,
                "metadata": {
                    "query": query,
                    "num_sources": len(sources),
                    "num_reasoning_steps": len(reasoning_trace)
                }
            }
            
        except Exception as e:
            logger.error(f"Error solving query '{query}': {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "message": str(e),
                "answer": None
            }
    
    def get_reasoning_explanation(self, trace: list) -> str:
        """
        Convert reasoning trace to human-readable explanation
        """
        if not trace:
            return "No reasoning steps available."
        
        explanation = "推理过程:\n"
        for i, step in enumerate(trace, 1):
            step_type = step.get("type", "unknown")
            step_desc = step.get("description", "")
            explanation += f"{i}. [{step_type}] {step_desc}\n"
        
        return explanation

# Singleton instance
kag_solver = KAGSolverService()

# Backward compatibility alias
kag_solver_service = kag_solver
