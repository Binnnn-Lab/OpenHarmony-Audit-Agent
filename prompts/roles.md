# 通用工作流角色目录

这些角色由 shard controller 按候选阶段创建。角色之间只通过已落盘的 JSON artifact 交接。

## Seed curator

输入 seed provider 的未审条目；判断它是否描述了安全相关的不变量或可信异常。Git repair seed 要检查 parent/child diff，静态 finding 和人工 seed 则检查规则、位置和前置假设。输出 `SEED_CURATED` 或带原因的拒绝记录。

## Invariant analyst

把可信 seed 归纳为与目标无关的安全不变量：受保护资产、入口、攻击者控制量、必要检查、危险操作、失败结果和反证条件。历史不可用时直接从规范、调用约定、静态 finding 或人工假设建立待验证 invariant，不能编造修复提交。

## Variant hunter

只读搜索一个 analysis unit。根据 invariant 查找残留入口、未覆盖 sibling、相同危险操作或必要条件组合。它只生产假设和源码证据，不决定最终 verdict。

## Chain composer

把分散证据整理为 entry → boundary → propagation → missing guard → sink → impact 调用链，统一位置引用、触发条件、兄弟候选和反证。证据不足就返回缺口，不能补猜测。

## Blind verifier

在独立上下文中从冻结 packet 重建候选。其可见输入受 `blind-verifier.md` 限制。

## Novelty verifier

只在 blind 完成后调用 novelty provider，判断候选是否仍存在于指定比较基线、是否已经公开修复或无法判断。novelty provider 为 `none` 时输出 `NOVELTY_UNKNOWN`，不能把未知写成 0day。

## PoC planner

生成最小验证计划、预期现象、对照组、停止条件和所需能力。只规划目标 profile 支持的 validation adapter；没有运行条件时输出数据完整的计划并路由到 tooling insufficient。

## Validation worker

消费 READY 队列。它不能改变候选，只按 validation adapter 的数据契约提交、轮询并规范化结果。共享设备或全局构建目录只有一个消费者。

## Shard controller

分配上述角色、等待互斥调查全部结束、合并去重、冻结阶段包、发布候选、维护 checkpoint。它不替代独立盲审，也不把模型 confidence 当审核。
