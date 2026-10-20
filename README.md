# OpenHarmony-Audit-Agent

OpenHarmony-Audit-Agent 将角色化代码审计工作流与 CodeQL-AI 的静态告警后处理能力统一为一套证据驱动的漏洞挖掘方案。

## 为什么要统一

静态分析适合高召回发现，但会受 sanitizer、分支约束和跨函数语义影响。审计工作流负责拆解入口、信任边界、调用链和漏洞不变量；CodeQL-AI 负责误报经验、QL 优化、清洗函数分析和聚焦式符号验证。两者通过统一的 `Finding → CandidatePacket → Evidence → Decision` 数据流协作。

## 快速开始

### HTML 原理与流程演示（推荐）

直接用浏览器打开 [frontend/demo.html](frontend/demo.html)，无需安装依赖或联网。八个章节串起两个工具的分工、Parcel 案例、路径约束实验、独立验证、经验反馈和实验设计，支持键盘推进、全屏、自动播放与讲解提示。讲解顺序见 [演示说明](frontend/DEMO.md)。

也可通过下方本地服务访问 http://127.0.0.1:8765/demo.html。

![HTML 原理演示：从静态告警到可追溯的证据与结论](docs/demo-story.png)

### 原有交互工作台（保留）

```shell
python scripts/serve_demo.py
```

打开 http://127.0.0.1:8765，体验可播放的审计流程、调用链与证据追踪、决策门禁实验和报告导出。前端使用纯静态文件，不需要 Node 构建或 API key。所有案例都标注为抽象演示，未连接实际审计引擎。详细讲解顺序见 [前端说明](frontend/README.md)。

![审计工作台：演示候选、七阶段工作流与统一证据链](docs/demo-workspace.png)

### Python 工具

```powershell
python -m pip install -e .
python -m openharmony_audit validate-target --target config/target.openharmony.abstract.json
python -m openharmony_audit prepare --target config/target.openharmony.abstract.json --run-root reports/run-data
python -m openharmony_audit report --output reports/technical-report.md --pdf reports/technical-report.pdf
```

CodeQL、angr、FastMCP 和 PDF 依赖均为可选能力，分别见 `pyproject.toml` 的 optional dependencies。当前抽象 profile 不绑定真实 OpenHarmony 源码、设备或漏洞结果。

## 目录

- `src/openharmony_audit/contracts`：统一 Campaign、Finding、Candidate、Evidence、Decision 和 Experience 契约。
- `src/openharmony_audit/workflow`：分片规划、阶段调度和 checkpoint。
- `src/openharmony_audit/engines/codeql`：CodeQL 命令和 SARIF 入口。
- `src/openharmony_audit/engines/codeql_ai`：内嵌的 CodeQL-AI provider 和可选 MCP 服务。
- `src/openharmony_audit/runtimes`：Claude Code 与 OpenAI-compatible 双 runtime。
- `src/openharmony_audit/evidence`：SARIF 归一化、provenance、经验库和决策门禁。
- `docs/technical-report.md`：中文技术方案主报告。
- `reports/technical-report.pdf`：由报告主稿生成的 PDF。

## 边界

PoC 首版只生成复现计划，不自动执行或披露。没有确定性动态证据的候选必须标记为 `STATIC_ONLY`。请阅读 `NOTICE.md` 了解来源和许可证边界。

