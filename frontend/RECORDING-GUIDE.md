# 环境与操作

## 打开和录制

将 03-recording-demo.html 保存到电脑，双击后用 Chrome、Edge、Firefox 或 Safari 打开。样式、图形、交互、环境说明和逐页讲稿都包含在这个文件中，支持离线查看。Windows、macOS 和 Linux 都可使用现代浏览器打开。

录屏时全屏展示网页，按自己的语速点击“继续演示”。第三页分五个步骤，第四页使用 32 / 64 / 96 快捷按钮和容量检查开关。顶部“逐页讲稿”可以查看全文；也可以在另一个窗口打开单独提供的讲稿文件。

## 运行环境

| 用途 | 环境 |
|---|---|
| 网页演示 | 现代浏览器；单个 HTML 文件离线打开 |
| 目标校验与任务准备 | Python 3.10+、pip；从源码目录安装基础包 |
| 主体审计 | Claude Code、可用模型与认证、目标源码；在 workflow 配置运行命令和模型 |
| 按需辅助检查 | CodeQL CLI、数据库和查询包；CodeQL-AI 对应的 FastMCP、angr 等依赖与目标产物 |

模型认证通过环境变量配置。审计目标填写源码路径、代码版本、分析单元和威胁模型。

## 安装

在源码根目录执行以下 Windows PowerShell 命令。macOS / Linux 的虚拟环境解释器路径为 .venv/bin/python。

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m openharmony_audit --help
```

## 常用命令

| 命令 | 用途 | 产物 |
|---|---|---|
| workflow validate | 检查目标和工作流配置 | 校验结果 |
| workflow plan | 查看任务分工 | worker 和分析单元的分配计划 |
| workflow prepare | 创建任务包 | plan.json、assignment.json、角色与检查点提示词 |
| workflow run | 启动已准备的审计任务 | 会话日志与任务状态 |
| workflow status | 查看任务进度 | 各 worker 的当前状态 |

下面两条命令用于抽象配置的校验与任务准备；--allow-missing-source 适用于这组抽象路径。

```powershell
.\.venv\Scripts\python.exe -m openharmony_audit workflow validate --workflow config/workflow.audit.example.json --target config/target.openharmony.abstract.json
.\.venv\Scripts\python.exe -m openharmony_audit workflow prepare --workflow config/workflow.audit.example.json --target config/target.openharmony.abstract.json --run-root reports/run-data --allow-missing-source
```

实际审计时填入目标源码与模型配置，prepare 使用实际源码校验，随后执行：

```powershell
.\.venv\Scripts\python.exe -m openharmony_audit workflow run --run-root reports/run-data
.\.venv\Scripts\python.exe -m openharmony_audit workflow status --run-root reports/run-data
```

## 网页操作

- 点击底部章节数字可跳转。左右方向键、PageUp / PageDown 可以推进或回看。
- 第三页点击“展开下一步”，依次查看五个角色步骤。
- 第四页点击 32、64、96 快捷按钮，或拖动长度滑块，再切换容量检查。
- N 显示本页操作提示，F 切换全屏，Escape 关闭说明或提示。
- “重新演示”恢复初始状态。网页刷新也会重新初始化示例。

## 示例设定

演示使用 Parcel 长度检查教学案例。任务交接通过网页状态变化呈现；约束实验计算 0–256 的整数输入，目标容量为 64。第七页展示评估方案，实际审计通过上面的命令在源码环境中运行。
