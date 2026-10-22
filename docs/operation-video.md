# 操作演示视频与配音

正式配音成片为 `deliverables/配音版操作演示视频.mp4`。原始画面视频为 `deliverables/03-operation-demo.mp4`，1920×1080、24 fps、无配音，18 段，共 8 分 34 秒。配套的 `03-operation-voiceover.html` 可以播放视频、按时间码跳转和查看正文。`03-operation-voiceover.md` 便于修改，SRT 可导入剪辑软件。

## 本次任务

- 目标：OpenHarmony 官方 `commonlibrary_c_utils`。
- 来源：https://github.com/openharmony/commonlibrary_c_utils
- 固定提交：`b807d3dadb7dbb7639fe85b3a5f72da18d318da2`。
- 目标文件：`base/src/parcel.cpp`，参考 `base/include/parcel.h`。
- 范围：WriteBuffer、EnsureWritableCapacity、WriteDataBytes 及四个直接辅助函数。
- 运行时：Codex CLI 0.163.0-alpha.10.2，模型配置为 `gpt-6-astra`，Python 3.14.0。
- 本次采用单个 worker，顺序做入口、数据流及保护条件检查。
- 结果：源码检查完成，候选数量 0，实际生成四份检查产物。
- 实测：129.60 秒；本地进程树最大采样 RSS 385.45 MiB；配置采样间隔 20 ms。

测量范围是这次小范围源码审计。内存口径为本地父进程与存活子进程 RSS 的采样和；共享页面可能重复统计，短峰值可能遗漏，远端模型资源另计。

## 画面来源

实际执行了安装、环境检查、validate、plan、prepare、run 和 status。命令输出、模型写入的检查结果和测量文件保存在 `reports/operation-demo/`。原始未整理日志留在本机 `tmp/operation-demo/`。

视频通过浏览器录制这些运行记录的回放和文件查看，再按配音时间剪辑。画面标明“本次运行记录回放”，机器路径以 `<PROJECT>`、`<USER>` 简写。第 16 段是容量约束教学交互；它解释辅助路径检查的原理。本次实际任务使用主体源码审计，CodeQL-AI 为可选辅助。

## 配音步骤

1. 解压 `03-operation-video-kit.zip`，保持视频与讲稿 HTML 在同一文件夹。
2. 打开 `03-operation-voiceover.html`，逐段试读。正文直接读，灰色画面提示供自己参考。
3. 每段开头约留两秒，按时间范围录音；可以在剪辑软件中分段摆放音轨。
4. 导入 `03-operation-voiceover.srt` 添加字幕，按自己的停顿微调。
5. 导出带本人配音的 MP4。

## 重现操作与制作

制作脚本使用 Python 3.11+（读取 TOML 配置），工具主体最低版本仍为 Python 3.10。安装基础包和 `benchmark` 可选依赖，准备已配置的 Codex CLI。使用 Windows 原生命令行可执行文件，运行时沿用本机认证目录，认证内容不写入任务配置。

```powershell
git clone https://github.com/openharmony/commonlibrary_c_utils.git tmp/demo-source-c-utils
git -C tmp/demo-source-c-utils checkout b807d3dadb7dbb7639fe85b3a5f72da18d318da2
python -m pip install -e ".[benchmark]"
python scripts/recording_session.py prepare
python scripts/recording_session.py audit
node scripts/build_operation_video.cjs
node scripts/capture_operation_video.cjs
python scripts/package_operation_video.py
```

`recording_session.py` 读取本机 Codex 配置中的模型名，生成本地配置，执行真实命令。脚本会保留已有任务；重新测量时为 prepare 和 audit 指定相同的新 `--session-dir tmp/operation-demo-2`，并用 `--export-dir reports/operation-demo-2` 保存新记录。录制脚本需要 Chrome、`frontend` 的 Puppeteer 依赖和 FFmpeg；通过 `FFMPEG_PATH` 指定 FFmpeg 路径。

Codex 接入依据：[官方非交互模式文档](https://developers.openai.com/codex/noninteractive/)。使用 `codex exec --json --ephemeral --sandbox workspace-write`，通过 stdin 传入任务，输出 JSONL 事件。

## 源码节选来源

视频和回放文件展示 Parcel 源码 409–432 行，版权为 `Copyright (c) 2021 Huawei Device Co., Ltd.`，原文件使用 Apache-2.0。完整许可证随录制材料包提供。项目自身的许可状态继续按 NOTICE.md 说明执行。
