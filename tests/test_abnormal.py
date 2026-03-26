# tests/test_abnormal.py
import pytest
from agent.graph import run_agent

@pytest.mark.asyncio
class TestAbnormalScenarios:
    """异常场景测试"""

    @pytest.mark.parametrize("query,expected_behavior", [
        ("查订单", "ask_for_order_id"),  # 缺少订单号
        ("我要退货", "ask_for_reason"),  # 缺少原因
        ("查一下优惠券", "proceed"),  # 可以直接查
    ])
    async def test_missing_slots(self, query, expected_behavior):
        """测试信息不完整的情况"""
        result = await run_agent(query)

        if expected_behavior == "ask_for_order_id":
            # 验证Agent是否主动询问订单号
            task_plan_str = " ".join(result["task_plan"])
            assert "订单号" in task_plan_str or "order" in task_plan_str.lower()

    async def test_invalid_order_id(self):
        """测试无效订单号"""
        result = await run_agent("查一下订单ORD999999")

        # 验证错误处理
        final_answer = result["final_answer"].lower()
        assert any(word in final_answer for word in ["不存在", "没有", "not found"])

    async def test_order_not_returnable(self):
        """测试不可退货的订单"""
        result = await run_agent("退货 ORD789012")  # ORD789012是待付款状态

        # 验证业务规则校验
        final_answer = result["final_answer"]
        # 应该提示"待付款状态不可退货"
        assert any(keyword in final_answer for keyword in ["状态", "不可", "无法"])