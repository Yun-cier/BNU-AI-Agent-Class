"""
s3_agent.py
版本：s3 - Agent 循环（老师给的参照版本，在此基础上完善）
要点：Agent 自己决定下一步。支持闲聊、执行系统命令、抓取网页。
回复格式：
  - 命令:XXX   → 执行系统命令
  - fetch:URL  → 抓取网页正文
  - 完成:XXX   → 任务完成并总结
  - 普通文本   → 闲聊回复
"""
from dotenv import load_dotenv; load_dotenv()
from openai import OpenAI
from bs4 import BeautifulSoup
import httpx
import os
import requests
import subprocess
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

model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")


def fetch_url(url: str, max_chars: int = 4000) -> str:
    """
    抓取指定 URL 的网页，提取正文文本并返回精简内容。
    """
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        resp = requests.get(
            url,
            headers=headers,
            timeout=20,
            proxies={"http": None, "https": None}  # 禁用系统代理，避免超时
        )
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or "utf-8"

        soup = BeautifulSoup(resp.text, "html.parser")

        # 移除脚本、样式、导航等无关标签
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        # 优先取 article 或 main 正文区域
        text = ""
        for main_tag in soup.find_all(["article", "main"]):
            text += main_tag.get_text(separator="\n", strip=True) + "\n"

        # 如果没有 article/main，则取整个 body 文本
        if not text.strip():
            text = soup.get_text(separator="\n", strip=True)

        # 压缩空行并截断长度
        lines = [line for line in text.splitlines() if line.strip()]
        text = "\n".join(lines)
        if len(text) > max_chars:
            text = text[:max_chars] + "\n...[内容已截断]"

        return f"网页抓取成功，内容如下：\n{text}"
    except Exception as e:
        return f"网页抓取失败：{e}"


# 系统提示词：定义 Agent 的能力和回复格式
messages = [{
    "role": "system",
    "content": """你是用户的得力助手，可以自然流畅地闲聊。
你具备联网能力和命令执行能力：
- 当需要查询网页内容时，请用 "fetch:URL" 的格式回复，我会帮你抓取网页正文。
- 当需要执行系统命令时，请用 "命令:XXX" 的格式回复（每次只发一条命令）。
- 当你认为任务已完成时，用 "完成:XXX" 的格式总结。
其他情况下，直接像正常助手一样回复用户即可。"""
}]

# 外层循环：等待用户输入新任务
while True:
    try:
        user_input = input("\n你：")
    except EOFError:
        print("\n[系统] 输入结束，退出 Agent。")
        break

    messages.append({"role": "user", "content": user_input})

    # 内层循环：Agent 自主执行，直到任务完成或进入闲聊
    while True:
        response = client.chat.completions.create(
            model=model,
            messages=messages
        )
        reply = response.choices[0].message.content
        messages.append({"role": "assistant", "content": reply})
        print(f"[AI] {reply}")

        stripped = reply.strip()

        # 情况 1：AI 表示任务完成
        if stripped.startswith("完成:"):
            break

        # 情况 2：AI 要抓取网页
        if stripped.startswith("fetch:"):
            url = stripped.split("fetch:", 1)[1].strip()
            result = fetch_url(url)
            display = result[:500] + "..." if len(result) > 500 else result
            print(f"[系统] {display}")
            messages.append({"role": "user", "content": f"抓取结果：{result}"})
            continue

        # 情况 3：AI 没有发命令 → 当作闲聊，等待用户下一句
        if "命令:" not in reply:
            break

        # 情况 4：AI 要执行系统命令
        command = reply.strip().split("命令:")[1].strip()
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True
        ).stdout
        print(f"[系统] {result}")
        messages.append({"role": "user", "content": f"执行完毕:{result}"})

# MIT License | 郑先隽，北师大心理学部教授，人本AI设计与创新
