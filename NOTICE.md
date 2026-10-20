# 来源与重构声明

本项目是在两个已有工具基础上进行的统一架构重构，当前仓库不依赖外部仓库运行：

1. `megakn1ght/audit-workflow-prompts`（来源 commit `7bd9cd9cbea555980b347bfd71bd5e4e75087b9b`）：提供通用审计工作流、目标 profile、角色提示词、候选冻结、盲验证和 checkpoint 机制。
2. `Binnnn-Lab/CodeQL-AI`（来源 commit `51dbf412f440f723746087588665646c0edadddd`）：提供 SARIF 处理、误报经验、QL 优化、函数级 sanitizer 和符号路径验证能力。

本仓库保留了必要实现并重新组织模块边界，新增统一契约、证据归一化、决策门禁、模型 runtime 和报告层。两个来源仓库当前未声明可继承的开源许可证，因此本私有仓库暂不新增开源许可证。公开发布或提交比赛前，应由项目所有者完成许可证和披露审查。

