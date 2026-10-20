# OpenHarmony-Audit-Agent

OpenHarmony-Audit-Agent 将角色化代码审计工作流与 CodeQL-AI 的静态告警后处理能力统一为一套证据驱动的漏洞挖掘方案。

## 为什么要统一

静态分析适合高召回发现，但会受 sanitizer、分支约束和跨函数语义影响。审计工作流负责拆解入口、信任边界、调用链和漏洞不变量；CodeQL-AI 负责误报经验、QL 优化、清洗函数分析和聚焦式符号验证。两者通过统一的 `Finding → CandidatePacket → Evidence → Decision` 数据流协作。

## 快速开始

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

