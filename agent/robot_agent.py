import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

# 1. 加载配置
load_dotenv()

# 2. 初始化 DeepSeek 模型
llm = ChatOpenAI(
    model= 'qwen-plus',
    openai_api_key=os.getenv('DASHSCOPE_API_KEY'),
    openai_api_base=os.getenv('DASHSCOPE_BASE_URL'),
)

# 3. 定义提示词模板
# MessagesPlaceholder 会在运行时被对话历史填充
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个乐于助人的 AI 助手。"),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{question}"),
])

# 4. 构建链
chain = prompt | llm

# 5. 管理内存：创建一个字典来存储不同用户的历史记录
store = {}


def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]


# 6. 使用 RunnableWithMessageHistory 包装我们的链
# 这样 LangChain 会自动处理历史记录的读取和更新
with_message_history = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="question",
    history_messages_key="history",
)

# 7. 进入对话循环
print("--- 已进入 DeepSeek 聊天模式 (输入 'exit' 退出) ---")
session_config = {"configurable": {"session_id": "user_001"}}  # 区分不同会话的 ID

while True:
    user_input = input("你: ")
    if user_input.lower() in ["exit", "quit", "退出"]:
        break

    # 调用带记忆的链
    response = with_message_history.invoke(
        {"question": user_input},
        config=session_config
    )

    print(f"AI: {response.content}\n")