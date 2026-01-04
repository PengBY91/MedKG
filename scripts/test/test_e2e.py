"""
End-to-End Integration Test for KAG
Tests the complete flow: Build -> Query
"""
import asyncio
import sys
import os
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.kag_medical_builder import kag_builder
from app.services.kag_solver_service import kag_solver

async def test_e2e():
    print("="*80)
    print("KAG End-to-End Integration Test")
    print("="*80)
    
    # Step 1: Build knowledge from document
    print("\n[Step 1] Building Knowledge Graph from Document...")
    print("-"*80)
    
    test_content = """
糖尿病是一种慢性代谢性疾病,主要特征是血糖水平持续升高。

主要症状:
1. 多饮 - 经常感到口渴,饮水量增加
2. 多尿 - 尿量和排尿次数明显增多
3. 多食 - 食欲亢进,进食量增加
4. 体重下降 - 尽管进食增多,体重反而减轻

治疗方法:
1. 药物治疗:
   - 二甲双胍:一线降糖药物,主要通过减少肝脏葡萄糖生成和改善胰岛素敏感性来降低血糖
   - 胰岛素:用于1型糖尿病和部分2型糖尿病患者
   - 格列美脲:磺脲类药物,刺激胰岛素分泌

2. 生活方式干预:
   - 控制饮食,减少糖分摄入
   - 规律运动,每周至少150分钟中等强度运动
   - 控制体重,维持健康BMI

并发症预防:
- 定期监测血糖
- 控制血压和血脂
- 定期进行眼底检查
- 注意足部护理
    """
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(test_content)
        temp_file = f.name
    
    try:
        print(f"Document created: {temp_file}")
        result = kag_builder.build_document(temp_file)
        print(f"Build Status: {result['status']}")
        print(f"Build Details: {result.get('details', 'N/A')}")
        
        if result['status'] != 'success':
            print(f"❌ Build failed: {result}")
            return
        
        print("✅ Knowledge graph built successfully!")
        
    except Exception as e:
        print(f"❌ Build error: {e}")
        import traceback
        traceback.print_exc()
        return
    finally:
        if os.path.exists(temp_file):
            os.unlink(temp_file)
    
    # Step 2: Query the knowledge graph
    print("\n[Step 2] Querying Knowledge Graph...")
    print("-"*80)
    
    test_queries = [
        "糖尿病的主要症状有哪些?",
        "二甲双胍的作用机制是什么?",
        "如何预防糖尿病并发症?"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n[Query {i}] {query}")
        print("-"*40)
        
        try:
            result = await kag_solver.solve_query(query)
            
            if result['status'] == 'success':
                print(f"✅ Answer: {result.get('answer', 'No answer')[:200]}...")
                print(f"   Sources: {result.get('metadata', {}).get('num_sources', 0)}")
                print(f"   Reasoning Steps: {result.get('metadata', {}).get('num_reasoning_steps', 0)}")
            else:
                print(f"❌ Query failed: {result.get('message', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Query error: {e}")
    
    print("\n" + "="*80)
    print("Integration Test Complete!")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(test_e2e())
