import asyncio
import sys
import os
import pandas as pd

# Add current dir to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.data_governance_service import DataGovernanceService
from app.services.quality_rule_engine import QualityRule

async def verify_governance():
    print("--- Verifying Governance System (Phase 2) ---")
    gov = DataGovernanceService()

    # 1. Test Asset Scanning
    print("\n1. Testing Asset Catalog Scan...")
    connection = {"type": "HIS", "host": "192.168.1.100"}
    new_assets = await gov.scan_assets(connection)
    print(f"Discovered {len(new_assets)} assets:")
    for a in new_assets:
        print(f" - [{a['type'].upper()}] {a['name']}: {a['description']}")

    # 2. Test Quality Check with Medical Logic
    target_asset = new_assets[1] # his_diagnosis_records
    print(f"\n2. Testing Quality Check on '{target_asset['name']}'...")
    
    test_data = [
        {"patient_id": "P001", "gender": "Male", "age": 45, "diagnosis": "Hypertension", "systolic_bp": 130, "diastolic_bp": 85},
        {"patient_id": "P002", "gender": "Female", "age": 30, "diagnosis": "Uterine Fibroids", "systolic_bp": 115, "diastolic_bp": 75},
        {"patient_id": "P003", "gender": "Male", "age": 60, "diagnosis": "Uterine Fibroids", "systolic_bp": 140, "diastolic_bp": 90}, # Violation: Gender/Diag
        {"patient_id": "P004", "gender": "Female", "age": 160, "diagnosis": "Pneumonia", "systolic_bp": 120, "diastolic_bp": 80},     # Violation: Age
        {"patient_id": "P005", "gender": "Male", "age": 50, "diagnosis": "Diabetes", "systolic_bp": 110, "diastolic_bp": 120}        # Violation: BP logic
    ]
    
    report = await gov.run_quality_check(target_asset["id"], test_data)
    
    print(f"Quality Score: {report['quality_score'] * 100}%")
    print(f"Total Violations: {report['failed_records']} records failed check.")
    
    print("\nViolations by Rule:")
    for rule_id, detail in report["violations_by_rule"].items():
        print(f" ❌ {rule_id} ({detail['name']}): {detail['count']} hits")
        print(f"   Reason: {detail['description']}")

    # 3. Verify Asset Update
    updated_asset = await gov.get_asset(target_asset["id"])
    print(f"\n3. Verifying Asset Metadata Persistence...")
    print(f"Asset '{updated_asset['name']}' quality score in registry: {updated_asset['quality_score']}")

if __name__ == "__main__":
    asyncio.run(verify_governance())
