# agent/graph.py
# - 为测试创建模拟LLM
import json
import re
from datetime import datetime
from typing import List, Any


class MockResponse:
    """模拟响应对象"""

    def __init__(self, content: str):
        self.content = content
        self.additional_kwargs = {}

    def __getattr__(self, name):
        return None


class MockLLM:
    """增强版Mock LLM，兼容所有参数并提供更健壮的模拟逻辑"""

    async def ainvoke(self, messages: List[Any], **kwargs) -> MockResponse:
        """
        模拟LLM调用，兼容所有关键字参数

        Args:
            messages: 消息列表
            **kwargs: 任何参数（functions, function_call等都会被忽略但记录）
        
        Returns:
            MockResponse: 模拟的LLM响应
        """
        content = messages[0].content
        print(f"  [MockLLM] {datetime.now().strftime('%H:%M:%S')} 处理")

        # 记录functions参数（调试用）
        if 'functions' in kwargs:
            print(f"  [MockLLM] 收到functions参数，包含 {len(kwargs['functions'])} 个工具定义")

        # 1. 意图识别请求
        if "intent" in content.lower() or "分析用户问题的意图" in content:
            return self._handle_intent_recognition(content)

        # 2. 生成最终回答请求
        elif "基于以下信息生成最终回答" in content:
            return self._handle_final_answer_generation(content)

        # 3. 任务分解请求
        elif "分解为具体的执行步骤" in content or "steps" in content.lower():
            return self._handle_task_decomposition(content)

        # 默认响应
        else:
            return MockResponse(json.dumps({"steps": ["处理用户请求"]}, ensure_ascii=False))

    def _handle_intent_recognition(self, content: str) -> MockResponse:
        """处理意图识别请求"""
        # 提取用户问题部分
        user_question_match = re.search(r'用户问题[：:]\s*(.+?)(?:\n|$)', content, re.DOTALL)
        if user_question_match:
            user_question = user_question_match.group(1).strip()
        else:
            user_question = content

        print(f"  [MockLLM] 用户问题: {user_question[:50]}...")

        # 尝试提取订单号
        order_id_match = re.search(r'ORD\d+', user_question)
        order_id = order_id_match.group(0) if order_id_match else "ORD123456"

        # 根据关键词返回意图
        if ("订单" in user_question and ("查" in user_question or "查询" in user_question)) or "查订单" in user_question or "查询订单" in user_question:
            return MockResponse(json.dumps({
                "intent": "query_order",
                "slots": {"order_id": order_id},
                "confidence": 0.95
            }, ensure_ascii=False))

        elif "退货" in user_question:
            # 检查是否为复合请求（包含优惠券）
            if "优惠券" in user_question:
                return MockResponse(json.dumps({
                    "intent": "return_request",
                    "slots": {"order_id": order_id,
                              "reason": "商品质量问题",
                              "need_coupon": True},
                    "confidence": 0.9
                }, ensure_ascii=False))
            else:
                return MockResponse(json.dumps({
                    "intent": "return_request",
                    "slots": {"order_id": order_id,
                              "reason": "商品质量问题"},
                    "confidence": 0.8
                }, ensure_ascii=False))

        elif "优惠券" in user_question:
            return MockResponse(json.dumps({
                "intent": "check_coupon",
                "slots": {},
                "confidence": 0.85
            }, ensure_ascii=False))

        elif "转人工" in user_question:
            return MockResponse(json.dumps({
                "intent": "transfer_human",
                "slots": {"reason": "用户要求转人工"},
                "confidence": 0.95
            }, ensure_ascii=False))

        else:
            return MockResponse(json.dumps({
                "intent": "general_qa",
                "slots": {},
                "confidence": 0.8
            }, ensure_ascii=False))

    def _handle_final_answer_generation(self, content: str) -> MockResponse:
        """处理最终回答生成请求"""
        # 尝试提取执行结果
        result_match = re.search(r'执行结果[：:]\s*(.+?)(?:\n|$)', content, re.DOTALL)
        if result_match:
            execution_result = result_match.group(1).strip()
            # 检查执行结果是否为错误响应
            if '"error"' in execution_result.lower():
                # 提取错误信息并生成友好的回答
                try:
                    error_data = json.loads(execution_result)
                    error_msg = error_data.get("error", "处理失败")
                    return MockResponse(f"抱歉，{error_msg}，请检查您的订单号或联系客服。")
                except:
                    return MockResponse(f"抱歉，处理您的请求时遇到问题：{execution_result[:50]}...")
            # 如果执行结果是JSON，直接返回它作为最终回答（简化）
            return MockResponse(execution_result)
        else:
            # 默认回答
            return MockResponse("您的请求已处理完成。")

    def _handle_task_decomposition(self, content: str) -> MockResponse:
        """处理任务分解请求"""
        content_lower = content.lower()
        
        # 辅助函数：检查内容是否包含关键词（中英文）
        def contains_keywords(text, keywords):
            text_lower = text.lower()
            # 将关键词都转换为小写进行比较
            lower_keywords = [kw.lower() for kw in keywords]
            
            # 改进的关键词检查：避免匹配工具名中的部分单词
            # 例如："check_coupon"包含"coupon"，但这是工具名，不是用户需求
            # 我们检查关键词是否作为独立单词出现（前后有空格/标点/字符串边界）
            for kw in lower_keywords:
                # 构建正则表达式模式：单词边界或中文上下文
                 # 对于中文，直接检查是否包含（中文没有明确的单词边界）
                 # 对于英文，检查单词边界
                 # 检查是否包含中文字符
                 has_chinese = any('\u4e00' <= c <= '\u9fff' for c in kw)
                 if has_chinese:
                     # 中文关键词：直接检查是否包含
                     if kw in text_lower:
                         # 进一步检查：确保不是工具名的一部分
                         # 例如：如果kw是"券"，避免匹配"check_coupon"
                         # 但"优惠券"不会出现在工具名中，所以可以直接返回True
                         return True
                 else:
                    # 英文关键词：使用单词边界检查
                    # 构建正则表达式模式：单词边界
                    import re
                    pattern = r'\b' + re.escape(kw) + r'\b'
                    if re.search(pattern, text_lower):
                        return True
            return False
        
        # 定义关键词映射
        order_keywords = ["订单", "查订单", "查询订单", "order", "query"]
        return_keywords = ["退货", "退换货", "退款", "return", "refund"]
        coupon_keywords = ["优惠券", "优惠", "折扣", "coupon", "discount"]
        human_keywords = ["人工", "客服", "转人工", "human", "transfer"]
        
        # 检查是否包含各类关键词
        has_order = contains_keywords(content, order_keywords)
        has_return = contains_keywords(content, return_keywords)
        has_coupon = contains_keywords(content, coupon_keywords)
        has_human = contains_keywords(content, human_keywords)
        
        # 根据关键词组合选择不同的分解方案
        # 1. 退货+优惠券复合场景（必须同时包含退货和优惠券关键词）
        if has_return and has_coupon:
            steps = [
                "调用query_order查询订单ORD123456",
                "调用return_request申请退货，原因为商品质量问题",
                "调用check_coupon查询用户可用优惠券",
                "整合退货结果和优惠信息返回给用户"
            ]
        
        # 2. 单纯退货场景（包含退货但不包含优惠券）
        elif has_return and not has_coupon:
            steps = [
                "调用query_order查询订单ORD123456",
                "调用return_request申请退货",
                "告知用户退货结果"
            ]
        
        # 3. 单纯查询订单场景（只包含订单查询，不涉及退货/优惠券）
        elif has_order and not has_return and not has_coupon:
            steps = ["调用query_order查询订单状态", "返回结果给用户"]
        
        # 4. 查询优惠券场景（只包含优惠券查询）
        elif has_coupon and not has_return:
            steps = ["调用check_coupon查询优惠券", "返回优惠信息"]
        
        # 5. 转人工场景
        elif has_human:
            steps = ["调用transfer_human转接人工客服", "告知用户已转接"]
        
        # 6. 默认场景
        else:
            steps = ["处理用户请求"]

        return MockResponse(json.dumps({"steps": steps}, ensure_ascii=False))