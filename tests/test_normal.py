# tests/test_normal.py
import pytest
from agent.graph import run_agent

@pytest.mark.asyncio
class TestNormalScenarios:
    """正常场景测试用例"""

    @pytest.mark.parametrize("query,expected_intent", [
        ("查一下我的订单ORD123456到哪里了", "query_order"),
        ("我想退货，订单号ORD789012，商品有质量问题", "return_request"),
        ("我有哪些优惠券可以用", "check_coupon"),
        ("帮我转人工客服", "transfer_human")
    ])
    async def test_intent_recognition(self, query, expected_intent):
        """测试意图识别准确性"""
        result = await run_agent(query)
        assert result["intent"] == expected_intent

    async def test_order_query_flow(self):
        """测试订单查询完整流程"""
        result = await run_agent("查一下订单ORD123456")

        # 验证意图识别
        assert result["intent"] == "query_order"

        # 验证任务分解 - 核心测试点
        assert len(result["task_plan"]) > 0
        assert any("query_order" in step for step in result["task_plan"])

        # 验证工具使用
        assert "query_order" in result["tools_used"]

        # 验证最终回答
        assert result["final_answer"] is not None

    async def test_return_request_flow(self):
        """测试退换货完整流程"""
        result = await run_agent("我要退货，订单号ORD123456，原因是商品破损")

        # 验证任务分解（展示点：Agent是否能分解复杂任务）
        assert len(result["task_plan"]) >= 2  # 应该包含多个步骤
        print(f"\n任务分解结果: {result['task_plan']}")

        # 验证工具链
        assert "return_request" in result["tools_used"]

        # 验证是否需要人工介入（某些退货场景可能需要）
        assert result["need_human"] is not None