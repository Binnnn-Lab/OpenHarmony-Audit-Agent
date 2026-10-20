# 通用审计 Checkpoint Prompt

你只负责把当前完整状态写入 `checkpoint.json`，不继续发现候选、不运行验证、不改变已冻结 artifact。

读取 `assignment.json`、`worker-state.json`、现有 candidate/verification artifact 和最近 controller stream。只记录已经落盘且可重放的事实。`checkpoint.json` 必须包含：

- campaign、target、worker 和 source identity；
- 当前 phase 与最后完成的阶段包；
- 每个 analysis unit 的 cursor、完成状态和已读范围；
- 已冻结 candidate ID/revision/verdict；
- 尚未完成的精确下一步及所需接口；
- 正在等待的验证任务或共享资源；
- 已知失败、阻塞和不能重复执行的动作；
- 恢复时应先读取的文件。

以临时文件加原子 rename 写入。写完后退出，不把 checkpoint 完成标记为审计终态。
