# Parcel 源码检查记录

版本：`b807d3dadb7dbb7639fe85b3a5f72da18d318da2`，HEAD 一致，所查文件无工作区修改。依据目标 profile 的 `interfaces.source`，按入口、数据流、保护条件顺序检查。以下位置除注明外均在 `base/src/parcel.cpp`。

WriteBuffer（409–432）：拒绝空指针、零长度及补齐加法回绕；容量和复制成功后才补齐。源区间有效性与别名约定待复核。

EnsureWritableCapacity（145–180）：检查可写状态、已有容量路径的空指针、新容量增长和分配结果。159 行加法边界需结合状态不变量复核，未确认漏洞。

WriteDataBytes（383–393）：将剩余容量传入 memcpy_s，仅成功后推进计数。库语义与源缓冲区寿命未验证。

GetWritableBytes（91–98）：先比较再相减，否则返回零。其他入口维护游标的方式未检查。

CalcNewCapacity（109–143）：按阈值扩容并限幅，调用方再次检查容量。极值与配置前提待复核。

GetPadSize（`base/include/parcel.h:819–823`）：计算四字节补齐量；入口另查回绕。未执行边界测试。

WritePadBytes（395–407）：掩码修改末尾四字节并推进计数；依赖上游预留空间。对齐与对象范围前提待复核。

结果：源码检查完成，候选为 0，不代表证明无漏洞。历史、静态分析、动态验证及新颖性接口均为 none；未编译、运行 PoC 或盲验证。证据仅为 STATIC_ONLY，供人工复核。
