"""
s5_skill.py
版本：s5 - 加专业 Skill
要点：同一个 Agent，换知识包。system = agent.md + skill.md。
本示例 Skill：用户研究助理。
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
    """抓取指定 URL 网页正文。"""
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
            proxies={"http": None, "https": None}
        )
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or "utf-8"

        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        text = ""
        for main_tag in soup.find_all(["article", "main"]):
            text += main_tag.get_text(separator="\n", strip=True) + "\n"
        if not text.strip():
            text = soup.get_text(separator="\n", strip=True)

        lines = [line for line in text.splitlines() if line.strip()]
        text = "\n".join(lines)
        if len(text) > max_chars:
            text = text[:max_chars] + "\n...[内容已截断]"

        return f"网页抓取成功，内容如下：\n{text}"
    except Exception as e:
        return f"网页抓取失败：{e}"


# 1. 读取 agent.md（通用规则）和 skill.md（专业知识），拼接成系统提示词
with open("agent.md", "r", encoding="utf-8") as f:
    agent_prompt = f.read()
with open("skill.md", "r", encoding="utf-8") as f:
    skill_prompt = f.read()

system_prompt = f"{agent_prompt}\n\n{skill_prompt}"
messages = [{"role": "system", "content": system_prompt}]

# 2. Agent 主循环
while True:
    try:
        user_input = input("\n你：")
    except EOFError:
        print("\n[系统] 输入结束，退出 Agent。")
        break

    messages.append({"role": "user", "content": user_input})

    while True:
        response = client.chat.completions.create(
            model=model,
            messages=messages
        )
        reply = response.choices[0].message.content
        messages.append({"role": "assistant", "content": reply})
        print(f"[AI] {reply}")

        stripped = reply.strip()

        if stripped.startswith("完成:"):
            break

        if stripped.startswith("fetch:"):
            url = stripped.split("fetch:", 1)[1].strip()
            result = fetch_url(url)
            display = result[:500] + "..." if len(result) > 500 else result
            print(f"[系统] {display}")
            messages.append({"role": "user", "content": f"抓取结果：{result}"})
            continue

        if "命令:" not in reply:
            break

        command = reply.strip().split("命令:")[1].strip()
        result = subprocess.run(command, shell=True, capture_output=True, text=True).stdout
        print(f"[系统] {result}")
        messages.append({"role": "user", "content": f"执行完毕:{result}"})

# MIT License | 郑先隽，北师大心理学部教授，人本AI设计与创新
