# c3_subagent.py - 选项B：代码审查员
# 对照真 Claude Code：这一步 = Task / 子 agent（派子任务去探索，只拿回摘要，保持主上下文干净）
from dotenv import load_dotenv; load_dotenv()
from openrouter import OpenRouter
import os, json, sys
sys.stdout.reconfigure(encoding='utf-8')  # 修复 Windows 控制台 gbk 编码问题

client = OpenRouter(api_key=os.getenv("OPENROUTER_API_KEY"))
MODEL = "deepseek/deepseek-chat"

def read_file(path):  return open(path, encoding="utf-8").read()
def bash(cmd):
    """执行 bash 命令，返回 utf-8 解码的输出；Windows 兼容常用 Linux 命令"""
    import subprocess
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
    except subprocess.TimeoutExpired:
        return "错误：命令执行超时"
    except Exception as e:
        return f"错误：{str(e)}"

def subagent(task):
    """
    子 Agent：专门的代码审查员。
    被派去 demo_project 读代码，找出潜在 bug，只把最终报告返回给主 Agent。
    """
    sub = [
        {"role": "system", "content": (
            "你是一位严谨的代码审查员。你的任务是阅读指定项目（demo_project）的源代码，"
            "找出其中潜在的逻辑错误、异常未处理、边界条件遗漏等问题。\n"
            "你必须只报告问题，绝对不要修改任何代码。\n"
            "你可以使用 bash 工具执行 ls、cat、grep 等命令来探索和读取文件。\n"
            "审查流程必须包含以下步骤：\n"
            "1. 先用 bash 列出 demo_project/notes_app/ 下的文件；\n"
            "2. 至少读取 3 个相关文件（如 cli.py, store.py, analyze.py）；\n"
            "3. 分析后给出详细审查报告。\n"
            "发现 bug 时，请明确指出：文件名、行号（如果可能）、问题描述、复现条件。\n"
            "如果没发现问题，也如实说「暂未发现明显 bug」。\n"
            "最终报告必须包含具体文件、具体函数、具体问题和修复建议，不能只写「审查报告」四个字。\n"
            "每次只回复一个 JSON，不要别的文字，不要 markdown；字符串值里别用英文双引号，要引用就用「」：\n"
            '- 执行命令：{"tool": "bash", "args": {"cmd": "..."}}\n'
            '- 完成：{"done": "完整审查报告内容，尽量详细"}'
        )},
        {"role": "user", "content": task}
    ]
    max_turns = 12
    for turn in range(max_turns):
        r = client.chat.send(model=MODEL, messages=sub).choices[0].message.content
        print(f"  [子 Agent 第 {turn+1} 轮] {r[:200]}")
        sub.append({"role": "assistant", "content": r})
        try:
            a = parse(r)
        except Exception:
            sub.append({"role": "user", "content": "请只回合法 JSON"})
            continue

        # 如果返回里有 done，直接结束
        if "done" in a:
            report = a["done"]
            if len(report) < 50:
                sub.append({"role": "user", "content": "报告太短，请重新给出完整、具体的审查报告，包含文件名、行号、问题描述和复现条件。"})
                continue
            return report

        # 如果需要调用 bash
        if "tool" in a and a["tool"] == "bash" and "args" in a and "cmd" in a["args"]:
            out = bash(a["args"]["cmd"])
            print(f"  [bash 结果] {out[:200]}")
            sub.append({"role": "user", "content": f"输出：\n{out}"})
            continue

        # 如果模型直接给了一个报告对象（如 audit_report/findings/issues），尝试提取为报告
        if any(k in a for k in ["issues", "findings", "detailed_analysis", "critical_findings", "audit_report"]):
            return json.dumps(a, ensure_ascii=False, indent=2)

        # 否则要求规范格式
        sub.append({"role": "user", "content": "请只返回上述两种 JSON 格式之一：执行 bash 命令，或用 done 给出最终报告。"})

    # 最后强制结束
    sub.append({"role": "user", "content": "时间到了，请立即用 {\"done\": \"你的完整审查报告\"} 结束。"})
    r = client.chat.send(model=MODEL, messages=sub).choices[0].message.content
    try:
        a = parse(r)
        if "done" in a:
            return a["done"]
    except Exception:
        pass
    return "子 Agent 审查超时，未能在规定轮数内输出完整报告。已读取文件但模型未规范收尾。"

TOOLS = {"read_file": read_file, "bash": bash, "subagent": subagent}

def parse(s):
    s = s.strip().strip("`").removeprefix("json").strip()
    return json.loads(s[s.find("{"): s.rfind("}") + 1])

SYSTEM = """你是主编程助手。每次只回复一个 JSON，不要别的文字，不要 markdown；字符串值里别用英文双引号，要引用就用「」：
- 读文件：{"tool": "read_file", "args": {"path": "..."}}
- 执行命令：{"tool": "bash", "args": {"cmd": "..."}}
- 派代码审查员：{"tool": "subagent", "args": {"task": "一句话描述要它独立完成的代码审查任务"}}
- 完成：{"done": "总结"}
当用户要求进行代码审查、检查代码质量、寻找潜在 bug 时，你应该调用 subagent 工具，并传入清晰的审查指令。
收到 subagent 的返回结果后，请直接、完整地转述给用户，不要擅自修改结论。"""

messages = [{"role": "system", "content": SYSTEM}]
while True:
    messages.append({"role": "user", "content": input("\n你：")})
    while True:
        reply = client.chat.send(model=MODEL, messages=messages).choices[0].message.content
        messages.append({"role": "assistant", "content": reply})
        try:
            action = parse(reply)
        except Exception:
            messages.append({"role": "user", "content": "上一条不是合法 JSON，请只回一个 JSON，别的都不要"})
            continue
        if "done" in action:
            print(f"[完成] {action['done']}")
            break
        name, args = action["tool"], action["args"]
        print(f"[调用] {name}({args})")
        result = TOOLS[name](**args)
        print(f"[结果] {result}")
        messages.append({"role": "user", "content": f"工具返回：\n{result}"})
        
