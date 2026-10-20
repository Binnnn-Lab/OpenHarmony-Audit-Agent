# 来源与重构声明

本项目以审计工作流为主体重构，CodeQL-AI 作为按需辅助验证能力。必要源码保留在本仓库，运行不要求另行克隆两个来源仓库；模型、CodeQL 等运行环境依赖仍按所用能力配置。

1. `megakn1ght/audit-workflow-prompts`（来源 commit `7bd9cd9cbea555980b347bfd71bd5e4e75087b9b`）：提供通用审计工作流、目标 profile、角色提示词、候选冻结、盲验证和 checkpoint 机制。
2. `Binnnn-Lab/CodeQL-AI`（来源 commit `51dbf412f440f723746087588665646c0edadddd`）：提供 SARIF 处理、误报经验、QL 优化、函数级 sanitizer 和符号路径验证能力。

本仓库保留必要实现并重新组织模块边界，修复主体工作流迁移入口、增加可选辅助调用策略，新增统一契约、证据归一化、审核规则、模型 runtime、说明书、演示及性能测量入口。自动辅助调用与完整实际审计仍需联调，详见 docs/integration-status.md。两个来源仓库当前未声明可继承的开源许可证，本私有仓库暂不新增开源许可证。来源与重构范围应随源码交付保留。

