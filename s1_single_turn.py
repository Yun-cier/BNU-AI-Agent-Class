"""
s1_single_turn.py
版本：s1 - 单轮对话
要点：用户输入一次，模型回答一次。没有历史记忆，每次调用只包含 system + 当前 user。
"""
from dotenv import load_dotenv; load_dotenv()
from openai import OpenAI
import httpx
import os
import sys
import io

# Windows 中文环境强制 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')

# 创建 DeepSeek 客户端
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
    http_client=httpx.Client(trust_env=False)
)

# 1. 接收用户输入
user_input = input("你：")

# 2. 构造 messages：system + user（只有当前一轮）
messages = [
    {"role": "system", "content": "你是一个友好的助手。"},
    {"role": "user", "content": user_input}
]

# 3. 调用模型
response = client.chat.completions.create(
    model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
    messages=messages
)

# 4. 输出回复
reply = response.choices[0].message.content
print(f"[AI] {reply}")

# MIT License | 郑先隽，北师大心理学部教授，人本AI设计与创新
