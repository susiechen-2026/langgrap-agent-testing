# evaluation/trajectory_analysis.py
import json
import re
from typing import List, Dict, Set


class AgentTrajectoryAnalyzer:
    """Agent轨迹分析 - 核心创新点"""

    def __init__(self):
        self.trajectories = []
        
        # 工具到关键词的映射（用于判断工具是否适合查询）
        self.tool_keywords = {
            "query_order": {"订单", "查订单", "订单状态", "订单号", "到哪里了", "查询订单", "查一下", "我的订单"},
            "return_request": {"退货", "退换货", "退款", "换货", "质量问题", "不想要", "申请退货", "退货申请"},
            "check_coupon": {"优惠券", "折扣", "优惠", "券", "打折", "可用优惠券", "有什么优惠"},
            "transfer_human": {"人工", "客服", "转人工", "人工客服", "真人", "专员", "转接人工", "找客服"}
        }
        

        
        # 已知工具列表
        self.known_tools = {"query_order", "return_request", "check_coupon", "transfer_human"}

    def record_trajectory(self, query: str, steps: List[str], tools: List[str], final: str):
        """记录Agent的执行轨迹"""
        self.trajectories.append({
            "query": query,
            "steps": steps,
            "tools": tools,
            "final": final
        })

    def analyze_reasoning_path(self, trajectory_idx: int = -1):
        """分析推理路径的合理性"""
        traj = self.trajectories[trajectory_idx]

        analysis = {
            "reasoning_quality": 0,
            "issues": []
        }

        # 1. 检查步骤连续性
        for i in range(len(traj["steps"]) - 1):
            step_i = traj["steps"][i]
            step_next = traj["steps"][i + 1]

            # 检查逻辑断裂
            if self._is_logical_break(step_i, step_next):
                analysis["issues"].append(f"步骤{i + 1}到{i + 2}逻辑断裂")

        # 2. 检查工具使用合理性
        for tool in traj["tools"]:
            if not self._is_tool_appropriate(tool, traj["query"]):
                analysis["issues"].append(f"工具{tool}使用不合理")

        # 计算推理质量分数
        analysis["reasoning_quality"] = 1.0 - (len(analysis["issues"]) * 0.2)
        analysis["reasoning_quality"] = max(0, analysis["reasoning_quality"])

        return analysis

    def _extract_tool_from_step(self, step: str) -> str:
        """从步骤文本中提取工具名
        
        只提取明确的工具调用步骤，非工具步骤返回空字符串
        工具调用步骤特征：
        1. 包含工具名（如query_order, check_coupon等）
        2. 或以'调用'开头+工具关键词
        """
        step_lower = step.lower()
        
        # 首先检查是否包含明确的工具名
        for tool in self.known_tools:
            if tool in step_lower:
                # 验证这是否真的是工具调用（不是偶然包含工具名）
                # 检查步骤是否包含调用相关的关键词
                if any(call_keyword in step_lower for call_keyword in ["调用", "使用", "执行", "运行"]):
                    return tool
                # 或者工具名出现在步骤开头附近（前20个字符）
                tool_index = step_lower.find(tool)
                if tool_index >= 0 and tool_index < 20:
                    return tool
        
        # 如果不包含明确工具名，检查是否为"调用"+关键词的模式
        if "调用" in step:
            # 检查是否是调用特定工具的步骤
            if any(keyword in step for keyword in ["订单", "查询订单", "查订单"]):
                return "query_order"
            elif any(keyword in step for keyword in ["退货", "退换货", "退款"]):
                return "return_request"
            elif any(keyword in step for keyword in ["优惠券", "优惠", "折扣"]):
                return "check_coupon"
            elif any(keyword in step for keyword in ["人工", "客服", "转人工"]):
                return "transfer_human"
        
        # 非工具步骤或无法识别，返回空字符串
        return ""

    def _step_contains_keywords(self, step: str, keywords: Set[str]) -> bool:
        """检查步骤是否包含指定的关键词"""
        return any(keyword in step for keyword in keywords)

    def _query_contains_keywords(self, query: str, keywords: Set[str]) -> bool:
        """检查查询是否包含指定的关键词"""
        return any(keyword in query for keyword in keywords)

    def _is_logical_break(self, step1: str, step2: str) -> bool:
        """判断两个步骤之间是否有逻辑断裂"""
        # 提取两个步骤的工具名
        tool1 = self._extract_tool_from_step(step1)
        tool2 = self._extract_tool_from_step(step2)
        
        # 如果无法识别工具，使用保守策略：不标记为断裂
        if not tool1 or not tool2:
            return False
        
        # 规则1：自我循环通常不合理（重复相同工具）
        if tool1 == tool2:
            return True
        
        # 规则2：转人工后不应再有其他步骤
        if tool1 == "transfer_human":
            return True
        
        # 规则3：某些反向顺序可能不合理
        if tool1 == "return_request" and tool2 == "query_order":
            # 退货后查订单可能不合理
            return True
        if tool1 == "check_coupon" and tool2 == "return_request":
            # 查优惠券后退货可能不合理
            return True
        if tool1 == "check_coupon" and tool2 == "query_order":
            # 查优惠券后查订单可能不合理
            return True
        
        # 规则4：检查步骤之间的语义连贯性
        # 如果两个步骤都提到订单相关关键词，认为是连贯的
        order_keywords = {"订单", "order", "ORD"}
        step1_has_order = any(kw in step1 for kw in order_keywords)
        step2_has_order = any(kw in step2 for kw in order_keywords)
        if step1_has_order and step2_has_order:
            return False  # 连贯
        
        # 默认情况：认为合理，不标记为断裂
        return False

    def _is_tool_appropriate(self, tool: str, query: str) -> bool:
        """判断工具使用是否合适"""
        # 检查工具是否在已知工具列表中
        if tool not in self.known_tools:
            return True  # 未知工具，保守判断为合适
        
        # 获取该工具对应的关键词
        tool_keywords = self.tool_keywords.get(tool, set())
        
        # 检查查询是否包含工具对应的关键词
        if self._query_contains_keywords(query, tool_keywords):
            return True
        
        # 如果查询不包含工具关键词，检查是否有其他工具的关键词更匹配
        # 例如：查询包含"订单"但使用了check_coupon工具
        for other_tool, keywords in self.tool_keywords.items():
            if other_tool == tool:
                continue
            if self._query_contains_keywords(query, keywords):
                # 发现更匹配的工具，当前工具可能不合适
                return False
        
        # 如果查询不包含任何工具的关键词，保守判断为合适
        return True

    def generate_trajectory_report(self):
        """生成轨迹分析报告"""
        report = []
        report.append("# Agent执行轨迹分析报告\n")

        for i, traj in enumerate(self.trajectories):
            report.append(f"## 轨迹 {i + 1}: {traj['query']}")
            report.append("### 执行步骤")
            for j, step in enumerate(traj["steps"], 1):
                report.append(f"{j}. {step}")

            report.append("### 工具使用")
            report.append(f"工具列表: {', '.join(traj['tools'])}")

            analysis = self.analyze_reasoning_path(i)
            report.append(f"### 分析结果")
            report.append(f"- 推理质量评分: {analysis['reasoning_quality']:.2f}")
            if analysis['issues']:
                report.append("- 发现问题:")
                for issue in analysis['issues']:
                    report.append(f"  * {issue}")

            report.append("")

        return "\n".join(report)