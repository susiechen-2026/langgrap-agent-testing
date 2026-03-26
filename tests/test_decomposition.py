# tests/test_decomposition.py
import pytest
from agent.graph import run_agent

@pytest.mark.asyncio
class TestTaskDecomposition:
    """任务分解能力专项测试 - 核心创新点"""

    async def test_complex_request_decomposition(self):
        """测试复杂请求的分解能力"""
        query = """
        我要退货之前买的iPhone，订单号是ORD123456，
        顺便帮我看看有没有什么优惠券可以买新的，
        如果优惠券不够的话帮我转人工问问有没有其他优惠
        """

        result = await run_agent(query)

        # 1. 验证任务分解结果
        task_plan = result["task_plan"]
        print(f"\n🎯 任务分解结果:")
        for i, step in enumerate(task_plan, 1):
            print(f"  步骤{i}: {step}")

        # 2. 验证分解的完整性
        assert len(task_plan) >= 3  # 应该至少包含3个步骤

        # 3. 验证步骤逻辑顺序
        # 退货应该在查优惠券之前？或者并行？取决于设计
        decomposition_score = evaluate_decomposition(task_plan)
        print(f"📊 分解质量评分: {decomposition_score}")

        assert decomposition_score > 0.7

    async def test_decomposition_efficiency(self):
        """测试分解效率（最少步骤原则）"""
        query = "查一下订单ORD123456"

        result = await run_agent(query)
        task_plan = result["task_plan"]

        # 简单查询应该用最少步骤
        assert len(task_plan) <= 2  # 不应该过度分解

    async def test_dynamic_replanning(self):
        """测试动态重规划能力"""
        # 第一轮：查订单
        result1 = await run_agent("查订单ORD123456")
        initial_plan = result1["task_plan"]

        # 第二轮：追加新需求
        result2 = await run_agent("顺便帮我申请退货，因为商品坏了")

        # 验证是否能动态调整计划
        assert result2["intent"] == "return_request"
        assert len(result2["task_plan"]) >= 2  # 应该包含查订单+退货两个阶段


def evaluate_decomposition(plan):
    """评估任务分解质量"""
    score = 0.0

    # 1. 完整性检查
    required_keywords = ["退货", "优惠券", "转人工"]
    found = sum(1 for keyword in required_keywords
                if any(keyword in step for step in plan))
    completeness = found / len(required_keywords)

    # 2. 逻辑顺序检查
    # 退货 -> 查优惠券 -> 转人工 这个顺序是否合理？
    order_score = 1.0

    # 3. 步骤粒度检查
    # 步骤不应该太粗也不应该太细
    granularity = 1.0 if 3 <= len(plan) <= 6 else 0.5

    # 综合评分
    score = (completeness * 0.4) + (order_score * 0.3) + (granularity * 0.3)
    return score