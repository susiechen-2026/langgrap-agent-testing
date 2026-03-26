# run_tests.py
import asyncio
import pytest
import sys
from datetime import datetime
from pathlib import Path
import os

# 添加项目根目录到系统路径（插入到最前面，确保优先级）
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)
from evaluation.trajectory_analysis import AgentTrajectoryAnalyzer
from evaluation.metrics import PerformanceMonitor, TrajectoryQualityMetric
from agent.graph import run_agent


async def run_agent_tests():
    """运行所有Agent测试并生成报告"""

    # 获取当前文件所在目录
    current_dir = Path(__file__).parent
    project_root = current_dir.parent

    # 创建报告目录
    report_dir = project_root / "reports" / "test_results"
    report_dir.mkdir(parents=True, exist_ok=True)

    # 生成时间戳
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 运行pytest测试
    print("🚀 开始执行Agent测试...")
    
    # pytest参数
    pytest_args = [
        str(current_dir),  # 测试目录（tests目录）
        "-v",
        f"--html={report_dir}/pytest_report_{timestamp}.html",
        "--self-contained-html",
        "--maxfail=3",
        "-ra",
    ]

    # 在异步中运行同步pytest
    loop = asyncio.get_event_loop()
    pytest_exit_code = await loop.run_in_executor(
        None,
        lambda: pytest.main(pytest_args)
    )
    
    if pytest_exit_code == 0:
        print("✅ Pytest测试全部通过！")
    else:
        print(f"⚠️ Pytest测试完成，但有失败用例，退出码: {pytest_exit_code}")

    # 分析轨迹
    print("\n🚀 开始收集和分析Agent执行轨迹...")
    analyzer = AgentTrajectoryAnalyzer()
    
    # 性能监控
    print("📊 初始化性能监控器...")
    performance_monitor = PerformanceMonitor()

    # 测试用例定义（查询、期望意图、期望工具）
    test_cases = [
        {
            "query": "查订单ORD123456",
            "expected_intent": "query_order",
            "expected_tools": ["query_order"],
            "description": "简单订单查询"
        },
        {
            "query": "退货ORD123456 顺便看看优惠券",
            "expected_intent": "return_request",
            "expected_tools": ["return_request", "check_coupon"],
            "description": "复合请求（退货+查优惠券）"
        },
        {
            "query": "查一下订单状态，然后帮我申请退货",
            "expected_intent": "return_request",
            "expected_tools": ["query_order", "return_request"],
            "description": "顺序请求（查订单+退货）"
        }
    ]

    # 收集轨迹数据和性能监控
    successful_queries = 0
    performance_data = []
    
    for test_case in test_cases:
        query = test_case["query"]
        expected_intent = test_case["expected_intent"]
        expected_tools = test_case["expected_tools"]
        description = test_case["description"]
        
        try:
            print(f"  执行测试 ({description}): {query[:30]}...")
            result = await run_agent(query)
            print(f"  执行测试结果:{result}")
            
            # 验证结果
            if result and "task_plan" in result:
                # 记录轨迹数据
                analyzer.record_trajectory(
                    query=query,
                    steps=result.get("task_plan", []),
                    tools=result.get("tools_used", []),
                    final=result.get("final_answer", "")
                )
                
                # 性能监控评估
                performance_result = performance_monitor.evaluate_agent_run(
                    query=query,
                    expected_intent=expected_intent,
                    expected_tools=expected_tools,
                    actual_result=result
                )
                performance_data.append(performance_result)
                
                successful_queries += 1

                # 打印调试信息
                print(f" ✅ 步骤数: {len(result.get('task_plan', []))}, "
                      f"工具数: {len(result.get('tools_used', []))}")
                print(f" 📊 性能评分 - 意图识别: {performance_result['intent_score']:.3f}, "
                      f"工具选择: {performance_result['tool_score']:.3f}")
            else:
                print(f" ⚠️ 结果格式异常: {result}")

        except Exception as e:
            print(f"  ❌ 执行失败: {e}")

    print(f"  成功收集 {successful_queries}/{len(test_cases)} 个轨迹")

    # 生成轨迹报告
    if successful_queries > 0:
        report = analyzer.generate_trajectory_report()
        report_path = report_dir / f"trajectory_report_{timestamp}.md"

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)

        print(f"\n📊 轨迹报告已生成: {report_path}")
        
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
        
        # 生成分析摘要（包含性能数据）
        await generate_analysis_summary(analyzer, report_dir, timestamp, performance_monitor)
    else:
        print("\n⚠️ 没有成功收集到轨迹数据")

    print(f"\n✅ 测试执行完成！报告已保存到: {report_dir}")

    return 0 #pytest_exit_code


async def generate_analysis_summary(analyzer, report_dir, timestamp, performance_monitor=None):
    """生成分析摘要（可包含性能数据）"""

    summary = []
    summary.append("# Agent测试分析摘要\n")
    summary.append(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 统计信息
    trajectories = analyzer.trajectories
    summary.append(f"## 统计信息")
    summary.append(f"- 总轨迹数: {len(trajectories)}")

    # 工具使用统计
    all_tools = []
    for traj in trajectories:
        all_tools.extend(traj.get("tools", []))

    tool_stats = {}
    for tool in all_tools:
        tool_stats[tool] = tool_stats.get(tool, 0) + 1

    if tool_stats:
        summary.append("\n## 工具使用统计")
        for tool, count in tool_stats.items():
            summary.append(f"- {tool}: {count}次")

    # 步骤数量统计
    step_counts = [len(traj.get("steps", [])) for traj in trajectories]
    if step_counts:
        avg_steps = sum(step_counts) / len(step_counts)
        summary.append(f"\n## 步骤统计")
        summary.append(f"- 平均步骤数: {avg_steps:.1f}")
        summary.append(f"- 最小步骤数: {min(step_counts)}")
        summary.append(f"- 最大步骤数: {max(step_counts)}")

    # 分析每个轨迹的质量
    summary.append("\n## 轨迹质量分析")
    for i, traj in enumerate(trajectories):
        steps = traj.get("steps", [])
        tools = traj.get("tools", [])

        quality_score = TrajectoryQualityMetric().calculate_quality_score(steps, tools)
        summary.append(f"\n### 轨迹 {i + 1}: {traj.get('query', '')[:50]}")
        summary.append(f"- 质量评分: {quality_score:.2f}")
        summary.append(f"- 步骤数: {len(steps)}")
        summary.append(f"- 工具数: {len(tools)}")

        if quality_score < 0.5:
            summary.append(f"- ⚠️ 需要优化: 步骤可能不够完整或逻辑有问题")

    # 性能指标分析（如果提供了性能监控器）
    if performance_monitor is not None:
        performance_summary = performance_monitor.get_summary_report()
        if "message" not in performance_summary:
            summary.append("\n## 性能指标分析")
            summary.append(f"- 总运行次数: {performance_summary.get('total_runs', 0)}")
            summary.append(f"- 平均意图识别分数: {performance_summary.get('average_intent_score', 0):.3f}")
            summary.append(f"- 平均工具选择分数: {performance_summary.get('average_tool_score', 0):.3f}")
            summary.append(f"- 平均任务分解分数: {performance_summary.get('average_decomposition_score', 0):.3f}")
            summary.append(f"- 平均决策准确分数: {performance_summary.get('average_decision_score', 0):.3f}")
            
            # 详细指标
            intent_details = performance_summary.get('intent_details', {})
            if intent_details:
                summary.append("\n### 意图识别详细指标")
                summary.append(f"- 精确率: {intent_details.get('precision', 0):.3f}")
                summary.append(f"- 召回率: {intent_details.get('recall', 0):.3f}")
                summary.append(f"- F1分数: {intent_details.get('f1_score', 0):.3f}")
                summary.append(f"- 准确率: {intent_details.get('accuracy', 0):.3f}")
            
            tool_details = performance_summary.get('tool_details', {})
            if tool_details:
                summary.append("\n### 工具选择详细指标")
                summary.append(f"- 精确率: {tool_details.get('precision', 0):.3f}")
                summary.append(f"- 召回率: {tool_details.get('recall', 0):.3f}")
                summary.append(f"- F1分数: {tool_details.get('f1_score', 0):.3f}")
                summary.append(f"- 准确率: {tool_details.get('accuracy', 0):.3f}")

    # 保存摘要
    summary_path = report_dir / f"analysis_summary_{timestamp}.md"
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("\n".join(summary))

    print(f"📋 分析摘要已生成: {summary_path}")




async def run_single_test(query):
    """运行单个测试并返回结果"""
    try:
        result = await run_agent(query)
        return {
            "query": query,
            "success": True,
            "result": result
        }
    except Exception as e:
        return {
            "query": query,
            "success": False,
            "error": str(e)
        }


async def run_parallel_tests(queries, max_concurrent=3):
    """并行运行测试"""
    semaphore = asyncio.Semaphore(max_concurrent)

    async def run_with_semaphore(query):
        async with semaphore:
            return await run_single_test(query)

    tasks = [run_with_semaphore(query) for query in queries]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    return results


if __name__ == "__main__":

    # 运行主函数
    exit_code = asyncio.run(run_agent_tests())
    sys.exit(exit_code)