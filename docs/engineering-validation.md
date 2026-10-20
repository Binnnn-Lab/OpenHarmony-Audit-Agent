# 工程交付检查记录

检查日期：2026-10-20。本记录只覆盖工程入口、抽象数据、文档与演示，不代表漏洞识别效果或真实源码审计已经通过验证。

| 项目 | 方法 | 结果 |
|---|---|---|
| Python 语法 | compileall：src、scripts | 通过 |
| 主体 CLI | 抽象目标 validate、plan、prepare、status | 通过；4 个分析单元分配给 2 个 worker，未启动模型 |
| 主体证据判定 | unittest：无 CodeQL 的源码候选、独立复核要求、错误版本/归属、决定性反证 | 通过 |
| SARIF 导入 | unittest：标准 physicalLocation、CWE 标签、source/sink、原始 codeFlows、多 run 标识 | 通过 |
| JSON Schema | Draft 2020-12 结构检查；抽象 target 与主体 workflow 配置校验 | 通过 |
| HTML 原理演示 | npm run test:demo：离线、8 章、5 个案例步骤、辅助交接、检查点、边界值、键盘与响应式 | 通过；无外部请求或页面异常 |
| 保留的工作台 | npm test：回放、筛选、证据弹窗、状态实验、导出、响应式 | 通过 |
| 阅读页 | manual、narration、performance：1440 / 390 宽度、目录锚点、横向溢出检查 | 通过；检查截图 |
| 三份 PDF | ReportLab 生成、文本提取、逐页 PNG 检查 | 4 / 4 / 3 页，均小于 10MB |
| 字幕视频 | 实际页面操作截图与 CLI 输出剪辑；Chrome 读取视频元数据 | 286 秒，1440 × 1080，15 fps，H.264；字幕，无配音 |
| 规划性能 | 3 种合成规模 × 3 次独立运行 | 9 次正常退出；原始 JSON 与 stdout 见 reports/performance |

自动测试命令：

```powershell
python -m compileall -q src scripts
python -m unittest discover -s tests -v
```

在 frontend 目录运行 npm ci、npm run test:demo；npm test 需要根目录的 scripts/serve_demo.py 正在服务。PDF 和视频的重建入口分别为 scripts/build_submission_pdfs.py 与 frontend/DEMO.md 中的命令。

未执行：真实 OpenHarmony 全流程审计、模型请求、CodeQL 建库/查询、angr 目标验证、设备复现、PoC 执行。provider/MCP 代码已保留，完整 Agent 调用与证据入库仍需目标环境联调。代码契约的序列化、配置 Schema 校验与真实候选证据可信性是不同检查范围。

提交目录包含文件哈希清单，源码包内包含对应 Git commit 与每个文件的 SHA-256。报告中的环境数据不含密钥，原始项目归属保留于 NOTICE.md。
