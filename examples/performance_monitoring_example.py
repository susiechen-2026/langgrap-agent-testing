#!/usr/bin/env python3
# examples/performance_monitoring_example.py
"""
性能监控指标使用示例

此文件演示如何在实际测试中使用新添加的精确率/召回率监控指标。
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from evaluation.metrics import PerformanceMonitor
from agent.graph import run_agent


class TestDataGenerator:
    """生成测试数据（模拟期望值和实际结果）"""
    
    @staticmethod
    def get_test_cases():
        """获取测试用例数据"""
        return [
            {
                "query": "查一下订单ORD123456",
                "expected_intent": "query_order",
                "expected_tools": ["query_order"],
                "description": "简单订单查询"
            },
            {
                "query": "我要退货，订单号ORD789012",
                "expected_intent": "return_request",
                "expected_tools": ["return_request"],
                "description": "退货请求"
            },
            {
                "query": "查一下优惠券有什么",
                "expected_intent": "check_coupon",
                "expected_tools": ["check_coupon"],
                "description": "优惠券查询"
            },
            {
                "query": "帮我转人工客服",
                "expected_intent": "transfer_human",
                "expected_tools": ["transfer_human"],
                "description": "转人工请求"
            },
            {
                "query": "我想查订单ORD123456然后申请退货",
                "expected_intent": "return_request",  # 可能识别为退货
                "expected_tools": ["query_order", "return_request"],
                "description": "复杂混合请求"
            }
        ]


async def run_performance_analysis():
    """运行性能分析"""
    print("🚀 开始Agent性能监控分析")
    print("=" * 60)
    
    # 创建性能监控器
    monitor = PerformanceMonitor()
    test_cases = TestDataGenerator.get_test_cases()
    
    print(f"📋 测试用例数量: {len(test_cases)}")
    print()
    
    # 运行每个测试用例并评估
    for i, test_case in enumerate(test_cases, 1):
        print(f"📝 测试用例 {i}/{len(test_cases)}: {test_case['description']}")
        print(f"   查询: {test_case['query']}")
        print(f"   期望意图: {test_case['expected_intent']}")
        print(f"   期望工具: {test_case['expected_tools']}")
        
        try:
            # 运行Agent（在实际项目中，这里应该调用真正的Agent）
            actual_result = await run_agent(test_case["query"])
            
            # 评估性能
            eval_result = monitor.evaluate_agent_run(
                query=test_case["query"],
                expected_intent=test_case["expected_intent"],
                expected_tools=test_case["expected_tools"],
                actual_result=actual_result
            )
            
            # 显示评估结果
            print(f"   ✅ Agent结果:")
            print(f"      识别意图: {actual_result.get('intent', '未识别')}")
            print(f"      使用工具: {actual_result.get('tools_used', [])}")
            print(f"      任务计划步骤数: {len(actual_result.get('task_plan', []))}")
            print(f"   📊 评估分数:")
            print(f"      意图识别: {eval_result['intent_score']:.3f}")
            print(f"      工具选择: {eval_result['tool_score']:.3f}")
            print(f"      任务分解: {eval_result['decomposition_score']:.3f}")
            print(f"      决策准确: {eval_result['decision_score']:.3f}")
            
        except Exception as e:
            print(f"   ❌ 测试失败: {e}")
        
        print()
    
    # 显示综合报告
    print("=" * 60)
    print("📈 综合性能报告")
    print("=" * 60)
    
    summary = monitor.get_summary_report()
    
    if "message" in summary and summary["message"] == "尚无性能数据":
        print("暂无性能数据")
        return
    
    print(f"📊 总运行次数: {summary['total_runs']}")
    print()
    print("📈 平均分数:")
    print(f"   意图识别: {summary['average_intent_score']:.3f}")
    print(f"   工具选择: {summary['average_tool_score']:.3f}")
    print(f"   任务分解: {summary['average_decomposition_score']:.3f}")
    print(f"   决策准确: {summary['average_decision_score']:.3f}")
    print()
    
    # 显示详细指标
    print("🔍 详细指标分析:")
    print()
    
    # 意图识别详情
    intent_details = summary['intent_details']
    print("1. 意图识别:")
    print(f"   精确率: {intent_details['precision']:.3f}")
    print(f"   召回率: {intent_details['recall']:.3f}")
    print(f"   F1分数: {intent_details['f1_score']:.3f}")
    print(f"   TP/FP/FN/TN: {intent_details['true_positives']}/{intent_details['false_positives']}/{intent_details['false_negatives']}/{intent_details['true_negatives']}")
    print()
    
    # 工具选择详情
    tool_details = summary['tool_details']
    print("2. 工具选择:")
    print(f"   精确率: {tool_details['precision']:.3f}")
    print(f"   召回率: {tool_details['recall']:.3f}")
    print(f"   F1分数: {tool_details['f1_score']:.3f}")
    print(f"   TP/FP/FN/TN: {tool_details['true_positives']}/{tool_details['false_positives']}/{tool_details['false_negatives']}/{tool_details['true_negatives']}")
    print()
    
    # 任务分解详情
    decomposition_details = summary['decomposition_details']
    print("3. 任务分解:")
    print(f"   精确率: {decomposition_details['precision']:.3f}")
    print(f"   召回率: {decomposition_details['recall']:.3f}")
    print(f"   F1分数: {decomposition_details['f1_score']:.3f}")
    print()
    
    # 导出报告
    report_file = monitor.export_report("performance_summary.json")
    print(f"💾 详细报告已导出到: {report_file}")


def demonstrate_individual_metrics():
    """演示单个指标类的使用"""
    print("🎯 单个指标类使用演示")
    print("=" * 60)
    
    from evaluation.metrics import (
        IntentRecognitionMetric, 
        ToolSelectionMetric,
        TaskDecompositionMetric
    )
    
    # 1. 意图识别指标演示
    print("1. 意图识别指标:")
    intent_metric = IntentRecognitionMetric(threshold=0.8)
    
    # 模拟测试数据
    class TestCase:
        def __init__(self, expected, actual):
            self.expected_intent = expected
            self.actual_intent = actual
    
    test_cases = [
        TestCase("query_order", "query_order"),  # 正确
        TestCase("query_order", "return_request"),  # 错误
        TestCase("return_request", "return_request"),  # 正确
    ]
    
    for i, tc in enumerate(test_cases, 1):
        score = intent_metric.measure(tc)
        print(f"   测试{i}: 期望={tc.expected_intent}, 实际={tc.actual_intent}, 得分={score:.3f}")
    
    report = intent_metric.evaluate_intent_batch(test_cases)
    print(f"   批量评估报告 - 精确率: {report['precision']:.3f}, 召回率: {report['recall']:.3f}")
    print()
    
    # 2. 工具选择指标演示
    print("2. 工具选择指标:")
    tool_metric = ToolSelectionMetric(threshold=0.85)
    
    class ToolTestCase:
        def __init__(self, expected, actual):
            self.expected_tools = expected
            self.actual_tools = actual
    
    tool_test_cases = [
        ToolTestCase(["query_order"], ["query_order"]),  # 完全正确
        ToolTestCase(["query_order", "return_request"], ["query_order", "check_coupon"]),  # 部分正确
        ToolTestCase(["check_coupon"], ["transfer_human"]),  # 完全错误
    ]
    
    for i, tc in enumerate(tool_test_cases, 1):
        score = tool_metric.measure(tc)
        print(f"   测试{i}: 期望={tc.expected_tools}, 实际={tc.actual_tools}, 得分={score:.3f}")
    
    tool_report = tool_metric.evaluate_tool_batch(tool_test_cases)
    print(f"   批量评估报告 - 精确率: {tool_report['precision']:.3f}, 召回率: {tool_report['recall']:.3f}")
    print()
    
    # 3. 任务分解指标演示
    print("3. 任务分解指标:")
    decomposition_metric = TaskDecompositionMetric(threshold=0.7)
    
    class DecompositionTestCase:
        def __init__(self, query, plan, intent):
            self.query = query
            self.task_plan = plan
            self.intent = intent
    
    decomposition_test_cases = [
        DecompositionTestCase(
            "查一下订单",
            ["调用query_order查询订单", "返回订单信息"],
            "query_order"
        ),
        DecompositionTestCase(
            "我要退货",
            ["验证退货资格", "创建退货申请", "返回退货结果"],
            "return_request"
        ),
    ]
    
    for i, tc in enumerate(decomposition_test_cases, 1):
        score = decomposition_metric.measure(tc)
        print(f"   测试{i}: 意图={tc.intent}, 步骤数={len(tc.task_plan)}, 得分={score:.3f}")
    
    decomposition_report = decomposition_metric.evaluate_decomposition_batch(decomposition_test_cases)
    print(f"   批量评估报告 - 平均分数: {decomposition_report['average_score']:.3f}, 测试用例数: {decomposition_report['total_cases']}")
    print()


if __name__ == "__main__":
    print("🤖 Agent性能监控系统演示")
    print("=" * 60)
    
    # 演示单个指标
    demonstrate_individual_metrics()
    
    print("=" * 60)
    print("🚀 开始实际Agent性能分析（需要运行真实Agent）")
    print("注: 以下部分需要运行真实的Agent，需要注释掉run_agent调用或提供Mock")
    print()
    
    # 实际运行性能分析（注释掉以避免错误）
    """
    try:
        asyncio.run(run_performance_analysis())
    except Exception as e:
        print(f"⚠️ 运行性能分析时出错: {e}")
        print("这可能是因为需要配置Agent环境或Mock LLM")
    """
    
    print("✅ 性能监控指标演示完成")
    print()
    print("💡 使用建议:")
    print("1. 在测试用例中使用PerformanceMonitor评估每次Agent运行")
    print("2. 定期导出性能报告以监控趋势")
    print("3. 设置阈值告警（如F1分数低于0.7时发出警告）")
    print("4. 结合轨迹分析工具进行深度问题诊断")