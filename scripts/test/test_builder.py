"""
Test script for KAG Medical Builder
"""
import asyncio
import sys
import os
import tempfile

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.kag_medical_builder import KAGMedicalBuilder
from app.core.config import settings

def test_builder():
    print("Testing KAG Medical Builder...")
    print(f"Project ID: {settings.KAG_PROJECT_ID}")
    print(f"KAG Host: {settings.KAG_HOST}")
    
    builder = KAGMedicalBuilder()
    
    # Create a temporary test file
    test_content = """
糖尿病是一种常见的慢性疾病。主要症状包括多饮、多尿、多食和体重下降。
治疗方法包括使用胰岛素和二甲双胍等药物。

糖尿病分为1型和2型。1型糖尿病通常在儿童或青少年时期发病，需要终身注射胰岛素。
2型糖尿病多见于成年人，可以通过饮食控制、运动和口服降糖药物治疗。

常用的降糖药物包括：
- 二甲双胍：一线降糖药物
- 格列美脲：磺脲类药物
- 阿卡波糖：α-葡萄糖苷酶抑制剂
    """
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(test_content)
        temp_file = f.name
    
    try:
        print(f"\nTest file created: {temp_file}")
        print("\nBuilding test document...")
        result = builder.build_document(temp_file)
        print(f"\nBuild result: {result}")
    except Exception as e:
        print(f"\nBuild failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up
        if os.path.exists(temp_file):
            os.unlink(temp_file)
            print(f"\nCleaned up temp file: {temp_file}")

if __name__ == "__main__":
    test_builder()
