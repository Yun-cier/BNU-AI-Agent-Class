"""
s0_minimal.py
版本：s0 - 最小 API 骨架
要点：只验证"环境能跑"。读取 .env，向模型发一次固定请求，打印回复。
"""
from dotenv import load_dotenv; load_dotenv()
from openai import OpenAI
import httpx
import os
import sys
import io

# Windows 中文环境强制 UTF-8，避免输入输出乱码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 1. 创建 DeepSeek 客户端（兼容 OpenAI SDK 格式）
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
    http_client=httpx.Client(trust_env=False)  # 禁用系统代理自动检测，防止超时
)

# 2. 构造固定 messages：system + user
messages = [
    {"role": "system", "content": "你是一个友好的助手。"},
    {"role": "user", "content": "你好，请用一句话介绍自己。"}
]

# 3. 调用模型
response = client.chat.completions.create(
    model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
    messages=messages
)

# 4. 打印回复
print(response.choices[0].message.content)

# MIT License | 郑先隽，北师大心理学部教授，人本AI设计与创新
