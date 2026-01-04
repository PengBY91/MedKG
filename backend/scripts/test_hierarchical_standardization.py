
import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
# Load env for Neo4j/OpenAI BEFORE imports
load_dotenv(Path(__file__).parent.parent / ".env")

from app.services.examination_kg_service import examination_kg_service
from app.services.examination_standardization_service import examination_service

async def test_hierarchical_flow():
    print("Initializing KG Service...")
    await examination_kg_service.initialize()
    
    test_cases = [
        ("左手正位", "DR"),
        ("胸部CT平扫", "CT"),
        ("双膝关节侧位", "DR")
    ]
    
    print("\n--- Starting Hierarchical Standardization Test ---\n")
    
    for exam, modality in test_cases:
        print(f"Input: {exam} [{modality}]")
        try:
            result = await examination_service._standardize_single(exam, modality)
            print(f"Result: {result}\n")
        except Exception as e:
            print(f"Error: {e}\n")
            
    await examination_kg_service.close()

if __name__ == "__main__":
    asyncio.run(test_hierarchical_flow())
