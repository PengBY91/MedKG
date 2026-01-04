
import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

from app.services.examination_kg_service import examination_kg_service
from app.services.examination_standardization_service import examination_service
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

async def repro_multi_exam():
    print("Initializing KG Service...")
    await examination_kg_service.initialize()
    
    # Test cases with multiple exams
    test_cases = [
        ("右侧肩关节MR平扫,左侧肩关节MR平扫", "MRI"),
        ("头颅CT平扫+胸部CT平扫", "CT") 
    ]
    
    print("\n--- Testing Multi-Exam Input (Baseline) ---\n")
    
    for exam, modality in test_cases:
        print(f"Input: {exam} [{modality}]")
        try:
            result = await examination_service._standardize_single(exam, modality)
            print(f"Result: {result}\n")
        except Exception as e:
            print(f"Error: {e}\n")
            
    await examination_kg_service.close()

if __name__ == "__main__":
    asyncio.run(repro_multi_exam())
