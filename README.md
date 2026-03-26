# LangGraph Agent 行为测试 Demo

一个使用 LangGraph 构建的客服 Agent 行为测试 Demo，专注于测试 Agent 的任务分解能力、决策准确性和异常处理能力。

## 🎯 项目目标

- **任务分解能力测试**: 验证 Agent 将复杂用户请求拆解为可执行步骤的能力
- **决策准确性评估**: 评估 Agent 在不同场景下的意图识别和工具选择准确性  
- **异常处理测试**: 测试 Agent 在边界条件和异常场景下的健壮性
- **评估体系构建**: 建立可量化的 Agent 行为评估指标

## ✨ 核心特性

- **多场景测试覆盖**: 正常场景、异常场景、边界条件全流程测试
- **模块化架构**: 清晰的意图识别 → 任务分解 → 工具执行 → 生成回答工作流
- **模拟与真实切换**: 支持 Mock LLM（测试）和真实 LLM（生产）无缝切换
- **全面评估指标**: 任务分解质量、工具选择准确性、决策准确性等多维度评估
- **详细轨迹分析**: 记录和分析 Agent 的完整执行轨迹，支持推理路径分析

## 🏗️ 系统架构

```
├── agent/                    # Agent 核心模块
│   ├── graph.py             # LangGraph 工作流定义
│   ├── state.py             # Agent 状态类型定义
│   ├── tools.py             # 工具函数定义
│   └── llmmock.py           # Mock LLM 实现（测试用）
├── evaluation/              # 评估模块
│   ├── metrics.py           # 评估指标定义
│   └── trajectory_analysis.py # 轨迹分析器
├── tests/                   # 测试套件
│   ├── test_normal.py       # 正常场景测试
│   ├── test_abnormal.py     # 异常场景测试
│   ├── test_boundary.py     # 边界条件测试
│   └── test_decomposition.py # 任务分解专项测试
└── reports/                 # 测试报告
```

### Agent 工作流程

1. **意图识别**: 分析用户查询，识别意图（查询订单、退货、查优惠券等）
2. **任务分解**: 将复杂请求拆解为具体执行步骤
3. **工具执行**: 按步骤调用相应工具函数
4. **错误处理**: 自动检测工具执行错误并优先返回
5. **生成回答**: 基于执行结果生成友好回答

## 🚀 快速开始

### 环境准备

```bash
# 1. 克隆项目
git clone <repository-url>
cd langgrap-agent-testing

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量（可选）
cp .env.example .env
# 编辑 .env 文件设置您的 API 密钥
```

### 运行测试

```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行特定测试类别
python -m pytest tests/test_normal.py -v      # 正常场景
python -m pytest tests/test_abnormal.py -v    # 异常场景
python -m pytest tests/test_decomposition.py -v # 任务分解专项

# 生成 HTML 测试报告
python -m pytest tests/ --html=reports/test_report.html --self-contained-html
```

### 使用 Agent

```python
import asyncio
from agent.graph import run_agent

async def main():
    # 简单查询
    result = await run_agent("查一下订单ORD123456")
    print(f"意图: {result['intent']}")
    print(f"回答: {result['final_answer']}")
    
    # 复杂请求
    result = await run_agent("退货ORD123456，商品质量问题，顺便看看优惠券")
    print(f"任务计划: {result['task_plan']}")
    print(f"使用工具: {result['tools_used']}")

asyncio.run(main())
```

## 🔧 配置说明

### 环境变量

```env
# LLM 配置
USE_MOCK_LLM=True  # 是否使用 Mock LLM（测试时建议为 True）
DASHSCOPE_API_KEY=your_api_key  # DashScope API 密钥
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# 日志配置
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

### Mock LLM 切换

项目默认使用 Mock LLM 以确保测试可重复性。要切换到真实 LLM：

1. 设置 `USE_MOCK_LLM=False`
2. 配置正确的 `DASHSCOPE_API_KEY` 和 `DASHSCOPE_BASE_URL`
3. 在 `agent/graph.py` 中调整 LLM 参数

## 📊 测试体系

### 测试分类

| 测试类别 | 文件 | 测试重点 |
|:---|:---|:---|
| **正常场景** | `test_normal.py` | 意图识别准确性、完整流程验证 |
| **异常场景** | `test_abnormal.py` | 错误处理、边界条件、缺失信息 |
| **边界条件** | `test_boundary.py` | 模糊意图、混合意图、超长对话 |
| **任务分解** | `test_decomposition.py` | 分解效率、复杂请求处理、动态重规划 |

### 评估指标

- **任务分解质量**: 完整性、逻辑性、粒度、可执行性
- **工具选择准确性**: 工具匹配准确率、参数提取正确性
- **决策准确性**: 意图识别准确率、错误处理适当性
- **推理质量**: 步骤连续性、逻辑合理性、问题发现

## 🛠️ 扩展开发

### 添加新工具

1. 在 `agent/tools.py` 中定义工具函数：

```python
def new_tool(param1: str, param2: str) -> str:
    """工具描述"""
    # 工具实现
    return json.dumps({"result": "success"})
```

2. 将工具添加到 `TOOLS` 列表：

```python
TOOLS = [
    # ... 现有工具
    {
        "name": "new_tool",
        "function": new_tool,
        "description": "新工具描述"
    }
]
```

3. 在 `agent/graph.py` 的 `get_tool_schema` 函数中添加参数定义

### 添加新测试

1. 选择适当的测试文件或创建新文件
2. 继承测试类并添加测试方法：

```python
async def test_new_scenario(self):
    """测试新场景"""
    result = await run_agent("测试查询")
    assert result["intent"] == "expected_intent"
    assert "expected_keyword" in result["final_answer"]
```

## 📈 性能与质量

### 当前状态

- **测试通过率**: 100% (17/17)
- **代码质量**: 完整的类型注解、清晰的模块划分
- **错误处理**: 优先错误返回、友好错误提示
- **可维护性**: 清晰的架构、详细的日志、完整的文档

### 优化亮点

1. **智能错误处理**: 自动检测工具执行错误，优先返回错误信息
2. **灵活配置**: 支持环境变量控制 Mock/真实 LLM 切换
3. **全面评估**: 多维度评估指标和详细的轨迹分析
4. **测试完备**: 覆盖正常、异常、边界全场景

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

请确保：
- 添加相应的测试用例
- 更新相关文档
- 遵循现有的代码风格

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🙏 致谢

- [LangGraph](https://github.com/langchain-ai/langgraph) - 强大的有状态 Agent 工作流框架
- [LangChain](https://github.com/langchain-ai/langchain) - LLM 应用开发框架
- [DeepEval](https://github.com/confident-ai/deepeval) - LLM 评估框架

---

**✨ 提示**: 本项目是 Agent 行为测试的 Demo，展示了如何系统性地测试和评估基于 LangGraph 的 Agent。可用于学习、研究和实际项目中的 Agent 测试方案构建。