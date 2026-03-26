import os
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

# 加载环境变量
load_dotenv()

llm = ChatOpenAI(
    model="qwen-plus",
    openai_api_key=os.getenv('DASHSCOPE_API_KEY'),
    openai_api_base=os.getenv('DASHSCOPE_BASE_URL'),
)

# 创建提示词模板
template = """
你是一位友好的助手。
请回答以下问题：

问题：{question}
回答：
"""
prompt = PromptTemplate.from_template(template)

# 使用 LCEL 语法创建链 (推荐方式)
# 结构：Prompt -> LLM -> 解析为字符串
chain = prompt | llm | StrOutputParser()

# 运行链
question = "LangChain 是什么？它有什么主要用途？"

response = chain.invoke({"question": question})

print("问题：", question)
print("-" * 20)
print("回答：", response)