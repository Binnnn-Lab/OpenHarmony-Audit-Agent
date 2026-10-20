# 题目一交付材料

作品：OpenHarmony-Audit-Agent。主体为角色化源码审计工作流，CodeQL-AI 按需辅助验证。

| 交付件 | 文件 | 说明 |
|---|---|---|
| 1 工具源代码 | 01-source.zip | 含源码、提示词、配置、测试、HTML 与复现脚本；清单与 SHA-256 在压缩包内 SOURCE-MANIFEST.json |
| 2 技术说明书 | 02-technical-manual.pdf | 原理、关键模块与实现说明；可编辑稿为 docs/technical-report.md |
| 3 使用说明书 | 03-user-manual.pdf | 依赖、安装、操作及故障处理；HTML 为 frontend/manual.html |
| 3 DEMO 视频与配音 | 03-operation-video-kit.zip | 推荐：1080p 无配音视频、时间码讲稿、字幕和运行记录，团队配音后导出 |
| 3 操作演示视频 | 03-operation-demo.mp4 | 8 分 34 秒，实际 Parcel 源码检查记录回放与原理交互 |
| 3 配音稿 | 03-operation-voiceover.html、.md、.srt | 对应视频的 18 段讲稿，HTML 可播放视频并按时间跳转 |
| 3 原理录制材料 | 03-recording-kit.zip | 保留：单文件原理演示网页、逐页口语讲稿及打开说明 |
| 3 演示网页 | 03-recording-demo.html | 内嵌样式、图形、交互、环境说明和讲稿；可单独复制到其他电脑离线打开 |
| 3 逐页讲稿 | 03-narration.html、03-narration.md | 八页正文直接朗读，操作提示单独标注 |
| 5 性能说明 | 05-performance.pdf | 合成单元规划测试、Parcel 限定函数审计实测及资源采样方法 |

配音时解压 03-operation-video-kit.zip，打开 03-operation-voiceover.html，按各段时间码读正文。视频和讲稿 HTML 放在同一目录，可边看边录。操作回放 03-operation-replay.html 为单文件，也可独立离线打开。完整制作说明见 docs/operation-video.md。

原理 HTML 与逐页讲稿提供交互讲解；03-demo-captioned.mp4 及对应 SRT 为原理操作演示存档。03-operation-demo.mp4 展示实际任务记录回放与原理交互。

源码、说明书、视频与运行记录构成工具材料。性能数据的测量范围为合成任务规划和限定函数审计；大规模全仓扫描尚无实测数据。官方要求对照见 docs/competition-checklist.md。

SHA256SUMS.txt 记录文件校验值。来源归属与重构范围见 NOTICE.md。
