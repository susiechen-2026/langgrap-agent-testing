# agent/tools.py
import json
import random
from datetime import datetime, timedelta

# 模拟订单数据库
ORDERS_DB = {
    "ORD123456": {
        "order_id": "ORD123456",
        "status": "已发货",
        "tracking": "SF1234567890",
        "items": ["iPhone 15"],
        "amount": 6999.00,
        "order_time": "2025-03-10 14:30:00"
    },
    "ORD789012": {
        "order_id": "ORD789012",
        "status": "待付款",
        "items": ["AirPods Pro"],
        "amount": 1999.00,
        "order_time": "2025-03-15 09:20:00"
    }
}


def query_order(order_id: str) -> str:
    """查询订单状态

    Args:
        order_id: 订单号
    """
    if order_id in ORDERS_DB:
        order = ORDERS_DB[order_id]
        return json.dumps(order, ensure_ascii=False)
    else:
        return json.dumps({"error": "订单不存在"}, ensure_ascii=False)


def return_request(order_id: str, reason: str, items: str = "全部") -> str:
    """申请退换货

    Args:
        order_id: 订单号
        reason: 退换货原因
        items: 要退的商品
    """
    if order_id not in ORDERS_DB:
        return json.dumps({"error": "订单不存在"}, ensure_ascii=False)

    order = ORDERS_DB[order_id]
    if order["status"] == "已发货":
        # 模拟创建退货单
        return_id = f"RET{random.randint(10000, 99999)}"
        return json.dumps({
            "success": True,
            "return_id": return_id,
            "message": f"退货申请已提交，退货单号：{return_id}"
        }, ensure_ascii=False)
    else:
        return json.dumps({
            "error": f"订单状态为{order['status']}，不可退货"
        }, ensure_ascii=False)


def check_coupon(user_id: str = "default") -> str:
    """查询可用优惠券

    Args:
        user_id: 用户ID
    """
    coupons = [
        {"id": "CP001", "name": "满100减10", "condition": "满100可用"},
        {"id": "CP002", "name": "8折券", "condition": "限部分商品"}
    ]
    return json.dumps({"coupons": coupons}, ensure_ascii=False)


def transfer_human(reason: str) -> str:
    """转接人工客服

    Args:
        reason: 转接原因
    """
    return json.dumps({
        "success": True,
        "message": "已为您转接人工客服，请稍候..."
    }, ensure_ascii=False)


# 工具注册
TOOLS = [
    {
        "name": "query_order",
        "description": "查询订单状态，需要订单号",
        "function": query_order
    },
    {
        "name": "return_request",
        "description": "申请退换货，需要订单号、退换货原因",
        "function": return_request
    },
    {
        "name": "check_coupon",
        "description": "查询用户可用优惠券",
        "function": check_coupon
    },
    {
        "name": "transfer_human",
        "description": "转接人工客服，用于复杂问题",
        "function": transfer_human
    }
]