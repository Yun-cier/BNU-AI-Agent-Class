# 对照真 Claude Code：这一步 = Read / Write / Bash 等专用工具（比全用 bash 更可控、可审计）
from dotenv import load_dotenv; load_dotenv()                       # 1. 读取 .env 里的 API 密钥
from openrouter import OpenRouter                                   # 2. 导入 OpenRouter SDK
import os, json, sys, subprocess                                    # 3. os 执行命令；json 解析协议
sys.stdout.reconfigure(encoding='utf-8')                            # 修复 Windows 控制台 gbk 编码问题

MODEL = "deepseek/deepseek-chat"                                    # 使用在中国地区可用的模型

def read_file(path):  return open(path, encoding="utf-8").read()   # 4. 工具：读文件（真 Claude Code 的 Read）
def write_file(path, text):                                        # 5. 工具：写文件（真 Claude Code 的 Write）
    open(path, "w", encoding="utf-8").write(text); return f"已写入 {path}"
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

TOOLS = {"read_file": read_file, "write_file": write_file, "bash": bash}  # 6. 工具箱：名字 → 函数
def parse(s):                                                      # 7. 容错解析：剥掉模型偶尔加的 ```json 包裹
    s = s.strip().strip("`").removeprefix("json").strip(); return json.loads(s[s.find("{"): s.rfind("}") + 1])

SYSTEM = """你是一个编程助手。每次只回复一个 JSON，不要别的文字，不要 markdown 包裹；字符串值里别用英文双引号，要引用就用「」：
- 读文件：{"tool": "read_file", "args": {"path": "..."}}
- 写文件：{"tool": "write_file", "args": {"path": "...", "text": "..."}}
- 执行命令：{"tool": "bash", "args": {"cmd": "..."}}
- 完成时：{"done": "总结"}
优先用 read_file / write_file 处理文件，它们比 bash 更安全可控。"""  # 8. 系统提示：告诉模型有哪些工具、何时用

client = OpenRouter(api_key=os.getenv("OPENROUTER_API_KEY"))        # 9. 创建客户端
messages = [{"role": "system", "content": SYSTEM}]                  # 10. 对话历史
while True:                                                         # 11. 外层循环：等新任务
    messages.append({"role": "user", "content": input("\n你：")})
    while True:                                                     # 12. 内层循环：自主执行
        reply = client.chat.send(model=MODEL, messages=messages).choices[0].message.content
        messages.append({"role": "assistant", "content": reply})
        try:                                                        # 13. 解析 JSON
            action = parse(reply)
        except Exception:                                           # 坏格式不崩：请模型重发（这就是加固）
            messages.append({"role": "user", "content": "上一条不是合法 JSON，请只回一个 JSON，别的都不要"}); continue
        if "done" in action:                                        # 14. 完成 → 跳出
            print(f"[完成] {action['done']}"); break
        name, args = action["tool"], action["args"]                 # 15. 取出工具名和参数
        print(f"[调用] {name}({args})")
        result = TOOLS[name](**args)                                # 16. 关键升级：按名字派发到对应工具函数
        print(f"[结果] {result}")
        messages.append({"role": "user", "content": f"工具返回：\n{result}"})  # 17. 结果反馈
# MIT License｜郑先隽，北京师范大学心理学部教授，人本AI设计与创新
