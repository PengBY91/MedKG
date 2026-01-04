"""
Test script for KAG Solver Service
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.kag_solver_service import KAGSolverService
from app.core.config import settings

async def test_solver():
    print("Testing KAG Solver Service...")
    print(f"Project ID: {settings.KAG_PROJECT_ID}")
    print(f"KAG Host: {settings.KAG_HOST}")
    
    solver = KAGSolverService()
    
    # Test queries
    test_queries = [
        "糖尿病的主要症状有哪些?",
        "二甲双胍的作用机制是什么?",
        "如何预防糖尿病并发症?"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"{'='*60}")
        
        try:
            result = await solver.solve_query(query)
            
            if result["status"] == "success":
                print(f"\nAnswer: {result['answer']}")
                print(f"\nSources: {result['metadata']['num_sources']}")
                print(f"Reasoning Steps: {result['metadata']['num_reasoning_steps']}")
                
                if result.get('reasoning_trace'):
                    print(f"\n{solver.get_reasoning_explanation(result['reasoning_trace'])}")
            else:
                print(f"\nError: {result['message']}")
                
        except Exception as e:
            print(f"\nFailed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_solver())
