# 对照真 Claude Code：这一步 = tool_use（模型返回结构化工具调用，我们用手写 JSON 做极简版）
from dotenv import load_dotenv; load_dotenv()                       # 1. 读取 .env 里的 API 密钥（和昨天 s3 一样）
from openrouter import OpenRouter                                   # 2. 导入 OpenRouter SDK
import os, json, sys, subprocess                                    # 3. os 执行命令；json 解析结构化协议；subprocess 处理编码
sys.stdout.reconfigure(encoding='utf-8')                            # 修复 Windows 控制台 gbk 编码问题

MODEL = "deepseek/deepseek-chat"                                    # 使用在中国地区可用的模型

SYSTEM = """你是一个编程助手。每次只回复一个 JSON，不要有别的文字，不要用 markdown 包裹；字符串值里别用英文双引号，要引用就用「」：
- 要执行命令时：{"tool": "bash", "args": {"cmd": "要执行的命令"}}
- 任务完成时：  {"done": "给用户的总结"}"""                             # 4. 系统提示词：把 s3 的"命令:/完成:"文本协议，升级成 JSON 协议

def bash(cmd):
    """执行命令，返回 utf-8 解码的输出；Windows 兼容常用 Linux 命令"""
    # 如果命令是读文件，直接用 Python 以 UTF-8 读取，避免 Windows 编码问题
    stripped = cmd.strip()
    if stripped.startswith("cat ") or stripped.startswith("type "):
        path = stripped.split(" ", 1)[1].strip()
        try:
            with open(path, encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"错误：无法读取文件 {path}: {str(e)}"
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=30)
        output = result.stdout + result.stderr
        return output.strip() if output.strip() else "(命令无输出)"
    except Exception as e:
        return f"错误：{str(e)}"

def parse(s):                                                      # 容错解析：模型偶尔会用 ```json 包裹，剥掉再解析
    s = s.strip().strip("`").removeprefix("json").strip(); return json.loads(s[s.find("{"): s.rfind("}") + 1])

client = OpenRouter(api_key=os.getenv("OPENROUTER_API_KEY"))        # 5. 创建客户端
messages = [{"role": "system", "content": SYSTEM}]                  # 6. 对话历史，第一条是系统提示
while True:                                                         # 7. 外层循环：等用户下达新任务
    messages.append({"role": "user", "content": input("\n你：")})     # 8. 用户输入存入历史
    while True:                                                     # 9. 内层循环：Agent 自主执行直到完成
        reply = client.chat.send(model=MODEL,
                                 messages=messages).choices[0].message.content  # 10. 调用模型，取回复
        messages.append({"role": "assistant", "content": reply})    # 11. AI 回复存入历史
        try:
            action = parse(reply)                                   # 12. 关键升级：把 JSON 文本解析成 Python 字典
        except Exception:
            messages.append({"role": "user", "content": "上一条不是合法 JSON，请只回一个 JSON，别的都不要"}); continue
        if "done" in action:                                        # 13. 如果是完成信号 → 跳出内层循环
            print(f"[完成] {action['done']}"); break
        cmd = action["args"]["cmd"]                                 # 14. 从结构化字段里取命令（不再靠字符串切割）
        print(f"[执行] {cmd}")
        result = bash(cmd)                                          # 15. 执行命令
        print(f"[结果] {result}")
        messages.append({"role": "user", "content": f"命令输出：\n{result}"})  # 16. 把结果反馈给 AI
# MIT License｜郑先隽，北京师范大学心理学部教授，人本AI设计与创新
