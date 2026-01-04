import os
import sys

# Ensure we can import from kag package
try:
    from kag.common.conf import KAG_CONFIG
except ImportError:
    print("Error: 'openspg-kag' package not installed or not found.")
    sys.exit(1)

def test_config_loading():
    config_path = "config/kag_config.yaml"
    if not os.path.exists(config_path):
        print(f"Error: {config_path} not found.")
        return

    print(f"Loading config from {config_path}...")
    try:
        KAG_CONFIG.initialize(prod=False, config_file=config_path)
        print("Success: KAG_CONFIG initialized.")
        
        # Verify specific keys
        project_ns = KAG_CONFIG.all_config.get("project", {}).get("namespace")
        print(f"Project Namespace: {project_ns}")
        
        builder_chain = KAG_CONFIG.all_config.get("unstructured_builder", {}).get("chain", {}).get("type")
        print(f"Builder Chain Type: {builder_chain}")
        
        assert project_ns == "MedicalGovernance"
        assert builder_chain == "unstructured_builder_chain"
        print("Verification PASSED.")
    except Exception as e:
        print(f"Verification FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_config_loading()
