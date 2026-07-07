"""
s2_multi_turn.py
版本：s2 - 多轮对话 + 记忆
要点：用 messages 列表保存完整对话历史，模型能根据上下文追问和回答。
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

# 1. 初始化对话历史，加入 system 提示词
messages = [{"role": "system", "content": "你是一个友好的助手，会记住对话上下文。"}]

print("开始聊天，按 Ctrl+C 或 Ctrl+D 退出。\n")

# 2. 外层循环：持续接收用户输入
while True:
    try:
        user_input = input("你：")
    except EOFError:
        print("\n[系统] 输入结束，退出聊天。")
        break

    # 3. 把用户输入加入历史
    messages.append({"role": "user", "content": user_input})

    # 4. 调用模型（携带完整历史）
    response = client.chat.completions.create(
        model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        messages=messages
    )

    # 5. 把模型回复加入历史并打印
    reply = response.choices[0].message.content
    messages.append({"role": "assistant", "content": reply})
    print(f"[AI] {reply}\n")

# MIT License | 郑先隽，北师大心理学部教授，人本AI设计与创新
