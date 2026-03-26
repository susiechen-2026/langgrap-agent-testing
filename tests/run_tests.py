# run_tests.py
from pathlib import Path
import sys

# 添加项目根目录到系统路径（插入到最前面，确保优先级）
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import json
from datetime import datetime
from evaluation.trajectory_analysis import AgentTrajectoryAnalyzer
from evaluation.metrics import PerformanceMonitor


async def run_agent_tests():
    """运行所有Agent测试并生成报告"""
    # 创建报告目录
    report_dir = Path("reports/test_results")
    report_dir.mkdir(parents=True, exist_ok=True)

    # 生成时间戳
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 运行pytest测试
    print("🚀 开始执行Agent测试...")
    pytest.main([
        "../tests/",
        f"--html={report_dir}/reports/test_results/pytest_report_{timestamp}.html",
        "--self-contained-html",
        "-v"
    ])

    # 分析轨迹
    print("🚀 开始手机测试中的轨迹数据...")
    analyzer = AgentTrajectoryAnalyzer()
    
    # 性能监控
    performance_monitor = PerformanceMonitor()

    # 这里应该从测试中收集轨迹数据
    # 简化示例
    # 测试用例定义（查询、期望意图、期望工具）
    test_cases = [
        {
            "query": "查订单ORD123456",
            "expected_intent": "query_order",
            "expected_tools": ["query_order"],
            "description": "简单订单查询"
        },
        {
            "query": "退货ORD123456 商品破损 顺便看看优惠券",
            "expected_intent": "return_request",
            "expected_tools": ["return_request", "check_coupon"],
            "description": "复合请求（退货+查优惠券）"
        }
    ]

    from agent.graph import run_agent
    for test_case in test_cases:
        query = test_case["query"]
        expected_intent = test_case["expected_intent"]
        expected_tools = test_case["expected_tools"]
        description = test_case["description"]
        
        print(f"  执行测试 ({description}): {query[:30]}...")
        result = await run_agent(query)
        
        # 记录轨迹数据
        analyzer.record_trajectory(
            query=query,
            steps=result["task_plan"],
            tools=result["tools_used"],
            final=result["final_answer"]
        )
        
        # 性能监控评估
        performance_result = performance_monitor.evaluate_agent_run(
            query=query,
            expected_intent=expected_intent,
            expected_tools=expected_tools,
            actual_result=result
        )
        
        print(f" ✅ 步骤数: {len(result.get('task_plan', []))}, "
              f"工具数: {len(result.get('tools_used', []))}")
        print(f" 📊 性能评分 - 意图识别: {performance_result['intent_score']:.3f}, "
              f"工具选择: {performance_result['tool_score']:.3f}")


    # 生成轨迹报告
    report = analyzer.generate_trajectory_report()
    trajectory_report_path = report_dir / f"trajectory_report_{timestamp}.md"
    with open(trajectory_report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"📊 轨迹报告已生成: {trajectory_report_path}")
    
    # 生成性能报告
    print("📈 生成性能监控报告...")
    performance_report_path = report_dir / f"performance_report_{timestamp}.json"
    performance_monitor.export_report(str(performance_report_path))
    print(f"📊 性能报告已生成: {performance_report_path}")
    
    # 打印性能摘要
    performance_summary = performance_monitor.get_summary_report()
    print(f"📋 性能摘要:")
    print(f"   总运行次数: {performance_summary.get('total_runs', 0)}")
    print(f"   平均意图识别分数: {performance_summary.get('average_intent_score', 0):.3f}")
    print(f"   平均工具选择分数: {performance_summary.get('average_tool_score', 0):.3f}")
    print(f"   平均任务分解分数: {performance_summary.get('average_decomposition_score', 0):.3f}")
    
    print(f"✅ 测试完成！报告已保存到 {report_dir}/")


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_agent_tests())