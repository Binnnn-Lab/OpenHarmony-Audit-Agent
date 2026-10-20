# CodeQL-AI 证据增强 Prompt

对冻结的 Candidate Packet 执行以下顺序：

1. 读取 SARIF path，确认 source、sink、ruleId、CWE 和 code flow；
2. 匹配历史 FP Experience，记录匹配分数和未匹配转移；
3. 查找路径上的潜在 sanitizer，并读取函数实现；
4. 在需要时生成完整 patched QL，原始 QL 不直接覆盖；
5. 对关键分支构造攻击谓词，调用聚焦式符号执行；
6. 将每一步包装成 Evidence，记录 producer、输入哈希和工具版本。

不要因为单次模型判断就删除告警。若验证条件缺失，返回 `NEEDS_EVIDENCE` 或 `STATIC_ONLY`。

