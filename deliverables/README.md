# 题目一交付材料

作品：OpenHarmony-Audit-Agent。主体为角色化源码审计工作流，CodeQL-AI 按需辅助验证。

| 交付件 | 文件 | 说明 |
|---|---|---|
| 1 工具源代码 | 01-source.zip | 含源码、提示词、配置、测试、HTML 与复现脚本；清单与 SHA-256 在压缩包内 SOURCE-MANIFEST.json |
| 2 技术说明书 | 02-technical-manual.pdf | 原理、关键模块与实现说明；可编辑稿为 docs/technical-report.md |
| 3 使用说明书 | 03-user-manual.pdf | 依赖、安装、操作及故障处理；HTML 为 frontend/manual.html |
| 3 DEMO 视频 | 03-demo-captioned.mp4 | 字幕版工程原型演示；实际浏览器操作画面与真实 dry-run 输出剪辑，无配音；章节字幕另附 03-demo-captioned.srt |
| 5 性能说明 | 05-performance.pdf | 规划模块实测及完整审计测量方法；实际大规模源码扫描数据待补 |

视频中的案例、辅助返回和 checkpoint 交互是浏览器演示状态。命令章节实际运行 validate、plan、prepare、status，不调用模型。视频不包含真实漏洞扫描或设备复现；团队可按 frontend/NARRATION.md 录制配音版，后续追加实际任务片段。

第 4 项漏洞分析报告由团队后续提供。第 5 项尚缺真实大规模审计耗时与内存，当前工程测量不能替代。完整对照见 docs/competition-checklist.md。

校验：SHA256SUMS.txt 记录交付文件哈希。提交前按当届上传页面确认命名与模板，填入真实队长姓名。来源归属与重构范围见 NOTICE.md。
