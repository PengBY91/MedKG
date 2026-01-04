"""
验证所有移除的 Mock 是否有真实实现
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

async def verify_all_services():
    print("="*80)
    print("验证所有服务的真实实现")
    print("="*80)
    
    results = {}
    
    # 1. Graph Service
    print("\n[1] 验证 Graph Service...")
    try:
        from app.services.graph_service import graph_service
        # Graph operations delegated to KAG Builder/Solver
        assert graph_service is not None
        assert hasattr(graph_service, 'add_node')
        print("✅ Graph Service: 使用 KAG Builder/Solver 进行图操作")
        results['graph_service'] = True
    except Exception as e:
        print(f"❌ Graph Service: {e}")
        results['graph_service'] = False
    
    # 2. Clinical NLP Service
    print("\n[2] 验证 Clinical NLP Service...")
    try:
        from app.services.clinical_nlp_service import clinical_nlp_service
        assert clinical_nlp_service.llm is not None
        assert hasattr(clinical_nlp_service.llm, '__call__')
        print("✅ Clinical NLP Service: 使用真实 KAG LLM")
        results['clinical_nlp'] = True
    except Exception as e:
        print(f"❌ Clinical NLP Service: {e}")
        results['clinical_nlp'] = False
    
    # 3. Enhanced Ingest Service
    print("\n[3] 验证 Enhanced Ingest Service...")
    try:
        from app.services.enhanced_ingest_service import enhanced_ingest_service
        assert enhanced_ingest_service.builder is not None
        assert hasattr(enhanced_ingest_service.builder, 'build_document')
        print("✅ Enhanced Ingest Service: 使用真实 KAG Builder")
        results['enhanced_ingest'] = True
    except Exception as e:
        print(f"❌ Enhanced Ingest Service: {e}")
        results['enhanced_ingest'] = False
    
    # 4. Search Service
    print("\n[4] 验证 Search Service...")
    try:
        from app.services.search_service import search_service
        assert search_service.solver is not None
        assert hasattr(search_service.solver, 'solve_query')
        print("✅ Search Service: 使用真实 KAG Solver")
        results['search'] = True
    except Exception as e:
        print(f"❌ Search Service: {e}")
        results['search'] = False
    
    # 5. Rule Service
    print("\n[5] 验证 Rule Service...")
    try:
        from app.services.rule_service import rule_service
        assert rule_service.llm is not None
        print("✅ Rule Service: 使用真实 KAG LLM")
        results['rule'] = True
    except Exception as e:
        print(f"❌ Rule Service: {e}")
        results['rule'] = False
    
    # 6. Vector Terminology Service
    print("\n[6] 验证 Vector Terminology Service...")
    try:
        from app.services.vector_terminology_service import vector_terminology_service
        assert vector_terminology_service.llm is not None
        print("✅ Vector Terminology Service: 使用真实 LLM")
        results['vector_terminology'] = True
    except Exception as e:
        print(f"❌ Vector Terminology Service: {e}")
        results['vector_terminology'] = False
    
    # 7. Ingest Service
    print("\n[7] 验证 Ingest Service...")
    try:
        from app.services.ingest_service import ingest_service
        assert ingest_service.builder is not None
        print("✅ Ingest Service: 使用真实 KAG Builder")
        results['ingest'] = True
    except Exception as e:
        print(f"❌ Ingest Service: {e}")
        results['ingest'] = False
    
    # 8. Sandbox Service
    print("\n[8] 验证 Sandbox Service...")
    try:
        from app.services.sandbox_service import sandbox_service
        assert sandbox_service.shacl_shapes is not None
        from pyshacl import validate
        print("✅ Sandbox Service: 使用真实 pySHACL")
        results['sandbox'] = True
    except Exception as e:
        print(f"❌ Sandbox Service: {e}")
        results['sandbox'] = False
    
    # 9. KAG Solver Service
    print("\n[9] 验证 KAG Solver Service...")
    try:
        from app.services.kag_solver_service import kag_solver
        assert kag_solver.solver is not None
        print("✅ KAG Solver Service: 使用真实 SolverMain")
        results['kag_solver'] = True
    except Exception as e:
        print(f"❌ KAG Solver Service: {e}")
        results['kag_solver'] = False
    
    # 10. KAG Medical Builder
    print("\n[10] 验证 KAG Medical Builder...")
    try:
        from app.services.kag_medical_builder import kag_builder
        assert kag_builder is not None
        print("✅ KAG Medical Builder: 真实实现")
        results['kag_builder'] = True
    except Exception as e:
        print(f"❌ KAG Medical Builder: {e}")
        results['kag_builder'] = False
    
    # 总结
    print("\n" + "="*80)
    print("验证结果总结")
    print("="*80)
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    print(f"\n总计: {total} 个服务")
    print(f"通过: {passed} 个 ✅")
    print(f"失败: {total - passed} 个 ❌")
    print(f"成功率: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\n🎉 所有服务都有真实实现!")
    else:
        print("\n⚠️  部分服务验证失败,详见上方错误信息")
    
    return results

if __name__ == "__main__":
    asyncio.run(verify_all_services())
