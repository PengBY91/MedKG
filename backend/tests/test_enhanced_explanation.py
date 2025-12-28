"""
Enhanced Explanation Service Test Suite

测试增强后的辅助决策问答功能
"""

import asyncio
import json
from app.services.explanation_service import ExplanationService
from app.adapters.neo4j_adapter import Neo4jAdapter
from app.adapters.mock_adapters import MockLLMProvider


async def test_query_policy_enhanced():
    """测试增强后的政策查询功能"""
    
    # 初始化服务
    graph_db = Neo4jAdapter()
    llm = MockLLMProvider()
    service = ExplanationService(graph_db, llm)
    
    # 测试问题列表
    test_questions = [
        "门诊透析费用有限额吗？",
        "糖尿病患者可以报销哪些费用？",
        "CT检查需要满足什么条件才能报销？",
        "血液透析450元是否超限？",
        "二型糖尿病的标准编码是什么？"
    ]
    
    print("=" * 80)
    print("增强版辅助决策问答测试")
    print("=" * 80)
    print()
    
    for idx, question in enumerate(test_questions, 1):
        print(f"\n{'=' * 80}")
        print(f"测试案例 {idx}: {question}")
        print('=' * 80)
        
        try:
            result = await service.query_policy(question)
            
            # 验证响应结构
            assert "question" in result, "缺少 question 字段"
            assert "answer" in result, "缺少 answer 字段"
            assert "sources" in result, "缺少 sources 字段"
            assert "entities" in result, "缺少 entities 字段"
            assert "reasoning_trace" in result, "缺少 reasoning_trace 字段"
            assert "metadata" in result, "缺少 metadata 字段"
            
            # 打印结果
            print(f"\n【问题】")
            print(f"{result['question']}")
            
            print(f"\n【识别的实体】")
            print(f"{', '.join(result['entities']) if result['entities'] else '无'}")
            
            print(f"\n【检索结果】")
            print(f"共检索到 {result['metadata']['retrieval_count']} 条规则")
            print(f"最终使用 {result['metadata']['final_sources']} 条规则")
            
            if result['sources']:
                print(f"\nTop-3 相关规则:")
                for i, source in enumerate(result['sources'][:3], 1):
                    print(f"  {i}. {source.get('name')} (评分: {source.get('score', 0):.2f})")
                    print(f"     来源: {source.get('source', 'unknown')}")
            
            print(f"\n【术语标准化】")
            if result.get('standard_terms'):
                for original, standard in result['standard_terms'].items():
                    print(f"  {original} → {standard}")
            else:
                print("  无")
            
            print(f"\n【推理链路】")
            for trace in result['reasoning_trace']:
                status_icon = "✓" if trace['status'] in ['Done', 'Success'] else "○"
                print(f"  {status_icon} {trace['step']}")
                print(f"     状态: {trace['status']}")
                print(f"     详情: {trace['detail']}")
            
            print(f"\n【KAG 推理】")
            kag_raw = result.get('kag_raw', {})
            if 'error' in kag_raw:
                print(f"  状态: 失败")
                print(f"  原因: {kag_raw['error']}")
            elif kag_raw.get('answer'):
                print(f"  状态: 成功")
                print(f"  结论: {kag_raw['answer'][:100]}...")
            else:
                print(f"  状态: 无结果")
            
            print(f"\n【生成答案】")
            answer = result['answer']
            # 截断长答案
            if len(answer) > 300:
                print(f"{answer[:300]}...")
            else:
                print(answer)
            
            print(f"\n【测试结果】✓ 通过")
            
        except Exception as e:
            print(f"\n【测试结果】✗ 失败")
            print(f"错误信息: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)


async def test_comparison():
    """对比优化前后的效果"""
    
    print("\n" + "=" * 80)
    print("优化前后效果对比测试")
    print("=" * 80)
    
    graph_db = Neo4jAdapter()
    llm = MockLLMProvider()
    service = ExplanationService(graph_db, llm)
    
    question = "门诊透析费用有限额吗？"
    
    print(f"\n测试问题: {question}")
    
    # 模拟优化前的简单检索
    print(f"\n【优化前 - 简单关键词检索】")
    simple_results = await graph_db._keyword_search(question)
    print(f"  检索结果数: {len(simple_results)}")
    if simple_results:
        print(f"  Top-1: {simple_results[0].get('name')} (评分: {simple_results[0].get('score', 0):.2f})")
    
    # 优化后的多路召回
    print(f"\n【优化后 - 多路召回】")
    enhanced_results = await graph_db.search_policies(question, top_k=10)
    print(f"  检索结果数: {len(enhanced_results)}")
    if enhanced_results:
        print(f"  Top-1: {enhanced_results[0].get('name')} (评分: {enhanced_results[0].get('score', 0):.2f})")
        print(f"  来源分布:")
        sources = {}
        for r in enhanced_results:
            src = r.get('source', 'unknown')
            sources[src] = sources.get(src, 0) + 1
        for src, count in sources.items():
            print(f"    - {src}: {count} 条")
    
    # 完整增强流程
    print(f"\n【优化后 - 完整增强流程】")
    result = await service.query_policy(question)
    print(f"  识别实体: {len(result['entities'])} 个")
    print(f"  标准化术语: {len(result.get('standard_terms', {}))} 个")
    print(f"  推理阶段: {len(result['reasoning_trace'])} 个")
    print(f"  KAG 推理: {'成功' if result['kag_raw'].get('answer') else '未执行'}")
    print(f"  答案长度: {len(result['answer'])} 字符")
    
    print("\n对比总结:")
    print(f"  召回提升: {len(simple_results)} → {len(enhanced_results)} 条 (+{len(enhanced_results) - len(simple_results)})")
    print(f"  功能增强: 基础检索 → 6阶段增强流程")
    print(f"  可解释性: 无 → 完整推理链路追踪")


async def test_edge_cases():
    """测试边界情况"""
    
    print("\n" + "=" * 80)
    print("边界情况测试")
    print("=" * 80)
    
    graph_db = Neo4jAdapter()
    llm = MockLLMProvider()
    service = ExplanationService(graph_db, llm)
    
    edge_cases = [
        ("空查询", ""),
        ("超长查询", "这是一个非常非常非常长的查询" * 20),
        ("无关查询", "今天天气怎么样？"),
        ("特殊字符", "门诊@#$%透析&*()费用"),
        ("纯数字", "12345"),
    ]
    
    for name, question in edge_cases:
        print(f"\n测试: {name}")
        print(f"输入: {question[:50]}..." if len(question) > 50 else f"输入: {question}")
        
        try:
            if not question.strip():
                print("结果: 跳过（空查询）")
                continue
                
            result = await service.query_policy(question)
            print(f"结果: ✓ 正常处理")
            print(f"  检索数: {result['metadata']['retrieval_count']}")
            print(f"  实体数: {len(result['entities'])}")
        except Exception as e:
            print(f"结果: ✗ 异常 - {str(e)}")


async def run_all_tests():
    """运行所有测试"""
    try:
        await test_query_policy_enhanced()
        await test_comparison()
        await test_edge_cases()
        
        print("\n" + "=" * 80)
        print("✓ 所有测试完成")
        print("=" * 80)
    except Exception as e:
        print(f"\n✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║        增强版辅助决策问答测试套件                                ║
    ║                                                               ║
    ║  测试内容:                                                     ║
    ║    1. 基本功能测试                                             ║
    ║    2. 优化前后对比                                             ║
    ║    3. 边界情况测试                                             ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    asyncio.run(run_all_tests())

