# 主体工作流与辅助验证的整合状态

项目主体来自 `audit-workflow-prompts`：分片总控组织源码调查、不变量提取、变体搜索、反证、候选冻结、独立盲验证、PoC 计划与 checkpoint。`CodeQL-AI` 是按需辅助能力，回答候选中的具体技术问题。

| 环节 | 代码或配置 | 当前实现 |
|---|---|---|
| 主体入口 | `cli.py` → `workflow/generic_cli.py` | `workflow validate/plan/prepare/run/status` |
| 目标与分片 | `generic_contracts.py`、`generic_adapters.py`、`generic_planner.py` | 读取目标、确定性分配 unit、生成独立 assignment 与提示词 |
| 角色调查 | `prompts/controller.md`、`roles.md` | 提供角色职责与产物交接协议；实际调查由配置的 Agent 执行 |
| 会话与恢复 | `generic_runner.py`、`checkpoint.py` | 启动 Claude Code 或 Codex、保存 JSONL 日志、检查终态和运行 checkpoint 会话；产物恢复依赖 Agent 遵守协议 |
| 可选辅助策略 | `prompts/openharmony/codeql-evidence.md` | 已注入生成的 worker 提示词；有具体问题与工具配置时按需调用 |
| 辅助 provider / MCP | `engines/codeql_ai/providers.py`、`mcp/server.py` | 保留原分析能力并提供接口；没有全自动调度、规范化与入库闭环 |
| 统一契约 | `contracts/models.py` | CandidatePacket、Evidence、Decision 等可序列化对象；冻结由协议及 revision 约定实现，并非不可变数据库 |
| 证据判定 | `evidence/decision_gate.py` | 源码审计可形成 STATIC_ONLY；确认需关联同版本、已复核的确定性记录与独立复核标志；支持决定性反证分支 |
| 运行时 | `runtimes/`、`generic_runner.py` | 独立 HTTP 适配器可单独使用；主体 runner 接入 Claude Code 和 Codex CLI，OpenAI-compatible HTTP 尚未接入该 runner |
| 输出报告 | `reporting/` | 生成技术说明书；具体漏洞报告按候选、证据和复核记录组织 |

## 主体能够独立推进的工作

没有 CodeQL 数据库或告警时，仍能创建审计任务、组织源码调查和角色复核。源码位置、调用链、不变量、攻击者边界和反证记录构成候选依据。工具能力缺失记录为验证缺口，不影响已具备条件的源码调查。

## 辅助能力的使用条件

总控为调用指定候选 ID、revision、snapshot、具体问题和输入引用。保护函数、路径约束、查询规则或既有误报模式与当前问题相关时，选择对应辅助能力。返回值应保留错误状态、来源和适用范围；不能仅凭返回值含有 `symbolic_reachability` 或 `reachable=false` 确认、排除漏洞。

当前决策函数检查结构字段与已复核状态，不验证来源文件的实际内容或密码学真实性。调用方必须核验原始证据后设置 `reviewed`。所有人工或模型提供的字段都不能天然视为可信证明。

## 演示与实现的对应

HTML 第二章模拟任务拆分、角色交接、辅助结果关联与断点续作。主体 CLI 的 validate/plan/prepare/status 可以独立操作；run 需要真实源码、配置模型和认证。2026-10-21 新增 Codex 实际运行记录：固定版本 c_utils 的 Parcel 小范围源码检查，三个目标函数和四个直接辅助函数，候选数量 0。输出源码记录、检查报告、检查点、完成状态及资源测量。该次采用单 worker 顺序检查，独立盲验证及 CodeQL-AI 辅助不在该次执行范围。详见 [操作演示](operation-video.md)。
