# Agent 作业：从最小调用到专业 Skill

本项目以郑先隽老师提供的 `s3_agent.py` 为参照，逐步实现从最小 API 调用到带专业 Skill 的完整 Agent。

## 版本路线

| 文件 | 版本 | 核心要点 |
|---|---|---|
| `s0_minimal.py` | s0 | 最小 API 骨架：读 `.env`，发一次固定请求 |
| `s1_single_turn.py` | s1 | 单轮对话：`input` 一次，模型回复一次 |
| `s2_multi_turn.py` | s2 | 多轮对话 + 记忆：`messages` 保存完整历史 |
| `s3_agent.py` | s3 | Agent 循环：支持命令执行、网页抓取、闲聊 |
| `s4_prompt_externalized.py` | s4 | Prompt 外置：系统提示词从 `agent.md` 读取 |
| `s5_skill.py` | s5 | 加专业 Skill：`system = agent.md + skill.md` |

## 环境配置

1. 安装 Python 3.10+
2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
3. 在项目根目录创建 `.env` 文件，写入：
   ```env
   DEEPSEEK_API_KEY=your_api_key_here
   DEEPSEEK_MODEL=deepseek-chat
   DEEPSEEK_BASE_URL=https://api.deepseek.com
   ```

> ⚠️ **不要上传 `.env` 文件到 GitHub！** 本仓库已配置 `.gitignore` 排除 `.env`。

## 运行方式

每个文件都可以单独运行：

```bash
python s0_minimal.py
python s1_single_turn.py
python s2_multi_turn.py
python s3_agent.py
python s4_prompt_externalized.py
python s5_skill.py
```

### 非交互式测试示例

```bash
echo "你好" | python s1_single_turn.py
printf "我叫小明\n我今年20岁\n" | python s2_multi_turn.py
echo "请列出当前目录" | python s3_agent.py
echo "请列出当前目录" | python s4_prompt_externalized.py
echo "帮我设计一个大学生学习APP的用户访谈提纲" | python s5_skill.py
```

## 文件说明

- `.env`：API Key 等敏感配置（不上传）
- `.gitignore`：排除 `.env`、`__pycache__` 等
- `requirements.txt`：项目依赖
- `agent.md`：s4/s5 使用的通用 Agent 规则
- `skill.md`：s5 使用的专业领域技能包（用户研究助理）
- `README.md`：本文件

## 设计说明

### s0 - s2：对话能力逐步增强

- **s0** 验证环境能否正常调用模型。
- **s1** 加入用户输入，但每轮都是独立的，模型记不住上下文。
- **s2** 用 `messages` 列表保存历史，实现真正的多轮对话。

### s3：Agent 循环

在 s2 的基础上加入「自主决策」：
- `命令:XXX` → 执行系统命令
- `fetch:URL` → 抓取网页正文
- `完成:XXX` → 结束当前任务
- 普通文本 → 闲聊

### s4：Prompt 外置

把 s3 中写死的系统提示词移到 `agent.md`，改能力时先改文档，无需修改代码。

### s5：专业 Skill

在 s4 的基础上再读取 `skill.md`，把通用规则与专业知识解耦，实现「同一个 Agent，换知识包」。

## 提交检查清单

- [ ] 每个 `s*.py` 都能单独运行
- [ ] `.env` 未被提交到 GitHub
- [ ] 模型名称已替换为你自己的
- [ ] 代码已 push 到自己的 GitHub 仓库

## License

MIT License | 郑先隽，北师大心理学部教授，人本AI设计与创新
