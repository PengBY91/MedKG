import sys
import os
import asyncio

# Add current dir to path to find 'app'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.vector_terminology_service import vector_terminology_service

async def main():
    print("--- Verifying Vector Analysis Service ---")
    
    # Path to resource
    csv_path = os.path.join(os.path.dirname(__file__), "app/resources/icd10_sample.csv")
    
    if not os.path.exists(csv_path):
        print(f"Error: Resource file not found at {csv_path}")
        return

    print("1. Initializing Service...")
    vector_terminology_service.initialize(csv_path)
    
    test_terms = [
        "Heart attack",          # Should match Acute myocardial infarction
        "Diabetes Type 2",       # Exact matchish
        "Stomach ache",          # Maybe Gastritis or Appendicitis?
        "High blood pressure",   # Hypertension
        "Broken leg",            # No match in sample
        "Myocardial infarction"  # Exact
    ]
    
    print(f"\n2. Testing normalization for terms: {test_terms}")
    results = await vector_terminology_service.normalize(test_terms)
    
    print("\n--- Results ---")
    for r in results:
        match_str = f"✅ [{r.get('code')}] {r.get('standard_name')}" if r.get('match_found') else f"❌ No match (Guess: {r.get('best_guess')})"
        print(f"Input: '{r['term']}' -> {match_str} (Conf: {r['confidence']})")

if __name__ == "__main__":
    asyncio.run(main())
