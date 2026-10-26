# Agent 应用工程 · 本地实验包

要求 Python 3.10+，只使用标准库。默认离线实验无网络、无真实模型、无 API 费用。agent_loop.py 的 --live 为额外的显式联网选项，可能产生费用，外部 API 兼容性未验证。所有订单与退款均为本地合成数据。

## 快速运行

在本目录运行：

```bash
python3 -m unittest discover -v
python3 lab.py evaluate --policy naive --out runs/naive.json
python3 lab.py evaluate --policy safe --out runs/safe.json
python3 lab.py compare runs/naive.json runs/safe.json
python3 lab.py trace runs/naive.json T06-response_lost
python3 lab.py cost
python3 gradient_lab.py
```

## 实验顺序

1. 第 4 章：运行两种配置，阅读逐任务 trace。
2. 第 5 章：检查工具输入、授权、业务规则与返回状态。
3. 第 8 章：用 cost 命令改变缓存量与假设单价，核对算术。
4. 第 10 章：阅读 tasks.json，增加边界案例并解释预期。
5. 第 11–12 章：故意破坏账本或回答状态，验证评分器能发现。
6. 第 14 章：阅读提交后响应丢失、参数冲突和并发幂等测试。
7. 第 15 章：比较 injection 场景的模拟导出事件。
8. 第 19–20 章：观察交叉熵和两候选 DPO 目标的变化。

## 验证边界

- naive 是故意不安全的完整教学配置，包括决策策略和工具保护缺失。不要用于真实服务。
- safe 是参考规则配置。它通过这些测试不等于真实大模型能通过。
- 两种配置同时改变策略与工具保护，属于整套系统比较，不能归因为提示词单一收益。
- 12 个合成任务没有统计代表性。Wilson 区间仅演示计算，不能解释为生产置信区间。
- local_runtime_ms 是本地 Python 模拟器耗时，不是模型 API 延迟。
- injection 只记录模拟导出标记，没有实际导出或网络访问。
- pending 在本地账本中预留退款余额；真实结算、失败释放和对账未实现。
- SQLite 事务演示并发控制，未实现跨服务分布式事务。
- gradient_lab.py 是小型分类器和两候选概率目标，不是 Transformer、LoRA 或大模型 RL 训练。

## 建议扩展

保留独立评分器和安全工具，再实现模型适配器。输入包含当时可见信息，输出为结构化工具调用或回答。固定模型与 SDK 版本，从环境变量读密钥。不要把认证身份交给模型填写。

扩展任务包括：多商品部分退款、政策版本、确认后参数变化、跨会话重复请求、租户隔离与检索评测。每个扩展先写契约和失败案例，再修改实现。

## 进阶实验

```bash
python3 agent_loop.py --confirmed --out runs/confirmed.json
python3 agent_loop.py --out runs/unconfirmed.json
python3 retrieval_lab.py
python3 stats_lab.py
```

agent_loop.py 默认使用固定重放响应。--confirmed 只为本地教学任务记录确认。真实 API 接入需自行配置 AGENT_API_BASE、AGENT_API_KEY、AGENT_MODEL，再显式使用 --live。不要在脚本、笔记或结果中保存凭据。

retrieval_lab.py 演示词项 BM25 与元数据过滤，不使用向量模型。stats_lab.py 演示配对簇 bootstrap，不能修复采样偏差。

## 审订 v1.1

43 项测试覆盖原有契约和出版审阅新增的反例。新增检查包括历史调用 ID 冲突的整轮预检、确认绑定订单与金额、最终回答 usage、账本状态与余额对账，以及题目内容指纹和评分器版本的一致性。HTTP 适配器拒绝重定向与未支持的结束原因；这些通过离线响应夹具验证，未声称已接通供应商。

`Executor` 的可信构造参数需要 `target_order_id` 和确认时的 `approved_amount_cents`。`--confirmed` 只表示批准本例 O-102 的 8,000 分退款，不授予任意订单权限。幂等键在本实验库里全局唯一；生产多租户系统需要另外设计命名空间与保留期限。旧版本评测 JSON 缺少内容指纹，请重新运行 evaluate，不能与新版直接比较。

本轮协议预检不代表多工具事务。参数或业务拒绝仍作为工具结果返回，先前合法动作不会自动回滚。总时间/token 预算、取消、持久化确认、上游结算与外部 API 兼容性仍需扩展验证。
