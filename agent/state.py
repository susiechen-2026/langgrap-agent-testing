# agent/state.py
from typing import List, Dict, Any, Optional
from typing_extensions import TypedDict

class AgentState(TypedDict):
    """Agent对话状态"""
    messages: List[Dict[str, str]]  # 对话历史
    intent: Optional[str]  # 用户意图
    slots: Dict[str, Any]  # 槽位信息
    tools_used: List[str]  # 已使用的工具
    task_plan: List[str]  # 任务分解计划
    current_step: int  # 当前步骤
    need_human: bool  # 是否需要转人工
    final_answer: Optional[str]  # 最终答案