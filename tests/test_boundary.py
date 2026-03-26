# tests/test_boundary.py
import pytest
from agent.graph import run_agent

@pytest.mark.asyncio
class TestBoundaryScenarios:
    """边界条件测试"""

    async def test_long_order_history(self):
        """测试超长对话历史"""
        result = None
        # 模拟多轮对话
        for i in range(15):
            query = f"帮我查订单 {i}"
            result = await run_agent(query)

        # 验证Agent是否还能正常工作
        assert result["final_answer"] is not None
        assert "tools_used" in result

    async def test_ambiguous_intent(self):
        """测试模糊意图"""
        ambiguous_queries = [
            "我的东西",  # 什么都没说清
            "帮我",  # 意图不明
            "那个...",  # 无效输入
        ]

        for query in ambiguous_queries:
            result = await run_agent(query)
            # 应该转一般问答或询问澄清
            assert result["intent"] in ["general_qa", None]

    async def test_mixed_intents(self):
        """测试混合意图"""
        result = await run_agent("查订单ORD123456，顺便看看有什么优惠券可以用")

        # 验证Agent是否能处理多意图
        # 理想情况：先处理订单查询，再查优惠券
        used_tools = result["tools_used"]
        print(f"使用的工具: {used_tools}")

        # 至少应该识别出主要意图
        assert result["intent"] is not None