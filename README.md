# Agent 应用工程

**从模型调用到可靠业务系统 · 审订 v1.1**

中文自学教材：6 篇、24 章、12 个附录，约 5.5 万个中文字符及代码；PDF 为 205 页 A5。

- [在线阅读](https://henryarch.github.io/agent-engineering-book/)
- [直接打开 PDF](https://henryarch.github.io/agent-engineering-book/agent-engineering.pdf)
- [逐章审阅记录](https://henryarch.github.io/agent-engineering-book/review.html)
- [下载全部材料](https://henryarch.github.io/agent-engineering-book/agent-engineering-complete.zip)
- [下载实验包](https://henryarch.github.io/agent-engineering-book/agent-engineering-lab.zip)
- [Markdown 源稿](agent-engineering-manuscript.md)

## 学习内容

1. 模型机制、API、结构化输出与 Agent 执行循环。
2. 工具契约、MCP、RAG、上下文、记忆与缓存。
3. 业务成功定义、数据集、评分器、配对实验与持续迭代。
4. 架构、幂等、状态恢复、权限与运行治理。
5. 训练决策、数据、SFT、LoRA、DPO 与强化学习的机制。
6. 综合项目、故障演练、学习路线与毕业答辩。

能力分级是教材提出的工程框架，不是统一行业职级。

## 如何使用

推荐先读前言与第 1–4 章，再运行实验。HTML 包含全文搜索、笔记、进度、收藏、24 道单选概念检查与 4 个交互实验，学习记录保存在浏览器本地，可导入导出。PDF 保留正文、练习和参考答案，提供 37 个阅读单元的书签导航。

```bash
cd lab
python3 -m unittest discover -v
python3 lab.py evaluate --policy naive --out runs/naive.json
python3 lab.py evaluate --policy safe --out runs/safe.json
python3 lab.py compare runs/naive.json runs/safe.json
python3 agent_loop.py --confirmed --out runs/confirmed.json
```

Python 3.10+，仅使用标准库。默认离线、合成数据、无真实资金操作。实验结果不是模型榜单，naive 与 safe 同时改变策略和工具保护，不能归因于提示词单独改进。

## 审阅与验证

发布前逐节复核全部正文和附录，修复执行循环、确认范围、评分器、版本比较、计量与适配器等问题。43 项 Python 测试通过；离线检索、簇 bootstrap、梯度概念实验与浏览器交互已复测。详细结论、来源状态和验证范围见[审阅记录](逐章审阅记录.md)。

真实模型 API、MCP 部署和大模型训练未执行。`--live` 是需自行配置且可能产生费用的扩展；默认不联网。代码是教学实现，不能直接用于生产退款。来源随版本变化，使用时核对官方文档。

内容由 AI 基于公开资料编写与修订，尚未经过独立专家同行评审。欢迎通过 Issues 提交可复现问题、来源纠正或学习反馈；提交时请勿附带密钥或真实个人数据。
