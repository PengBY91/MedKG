import sys
import os
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent))

try:
    from app.core.config import settings
    
    print("=== Config Verification ===")
    print(f"KAG_PROJECT_ID: {settings.KAG_PROJECT_ID}")
    print(f"KAG_HOST: {settings.KAG_HOST}")
    print(f"KAG_NAMESPACE: {settings.KAG_NAMESPACE}")
    
    # Expected values from kag_config.yaml
    expected_id = "1"
    expected_host = "http://127.0.0.1:8887"
    expected_ns = "MedicalGovernance"
    
    assert settings.KAG_PROJECT_ID == expected_id, f"Expected ID {expected_id}, got {settings.KAG_PROJECT_ID}"
    assert settings.KAG_HOST == expected_host, f"Expected Host {expected_host}, got {settings.KAG_HOST}"
    assert settings.KAG_NAMESPACE == expected_ns, f"Expected Namespace {expected_ns}, got {settings.KAG_NAMESPACE}"
    
    print("\nSUCCESS: Configuration loaded correctly from kag_config.yaml")

except ImportError as e:
    print(f"Import Error: {e}")
    print("Ensure you are running this from the correct environment/path.")
except AssertionError as e:
    print(f"\nFAILURE: {e}")
except Exception as e:
    print(f"\nERROR: {e}")
