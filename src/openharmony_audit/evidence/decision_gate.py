"""Conservative decision policy for candidate packets."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from openharmony_audit.contracts.models import CandidatePacket, Decision


def evaluate_candidate(
    candidate: CandidatePacket,
    *,
    evidence: Iterable[Mapping[str, Any]],
    blind_verification: bool = False,
) -> Decision:
    """Return a reportable verdict without treating model confidence as proof."""
    items = [item for item in evidence if item.get("status", "available") == "available"
             and item.get("candidate_id") == candidate.candidate_id]
    kinds = {str(item.get("kind")) for item in items if item.get("status", "available") == "available"}
    refs = [str(item.get("evidence_id")) for item in items if item.get("evidence_id")]
    def reviewed_result(item: Mapping[str, Any], result: str) -> bool:
        content = item.get("content", {})
        return (isinstance(content, Mapping)
                and bool(item.get("source_ref"))
                and bool(item.get("input_hash"))
                and bool(item.get("content_hash"))
                and content.get("snapshot_id") == candidate.snapshot_id
                and content.get("candidate_revision") == candidate.revision
                and content.get("reviewed") is True
                and content.get("result") == result)
    if any(item.get("kind") == "decisive_counterevidence" and reviewed_result(item, "refuted") for item in items):
        return Decision(candidate.candidate_id, "REJECTED", "同一候选版本有已复核的决定性反证", refs, [], "medium")
    if not kinds.intersection({"source_review", "static_path", "sarif_alert"}):
        return Decision(candidate.candidate_id, "NEEDS_EVIDENCE", "缺少关联到候选的源码审计或静态路径证据", refs, ["source_review or static_path"], "low")
    if not candidate.call_chain or not candidate.locations:
        return Decision(candidate.candidate_id, "NEEDS_EVIDENCE", "源码位置或调用链不完整", refs, ["locations", "call_chain"], "low")
    if not candidate.invariant or not candidate.threat_model:
        return Decision(candidate.candidate_id, "NEEDS_EVIDENCE", "漏洞不变量或威胁边界不完整", refs, ["invariant", "threat_model"], "low")
    if len(candidate.counter_evidence) < 2:
        return Decision(candidate.candidate_id, "NEEDS_EVIDENCE", "尚未完成至少两条反证检查", refs, ["counter_evidence"], "low")
    deterministic = {"symbolic_reachability", "poc_execution", "deterministic_verification"}
    if blind_verification and any(item.get("kind") in deterministic and reviewed_result(item, "supported") for item in items):
        return Decision(candidate.candidate_id, "CONFIRMED", "源码审计、独立复核与同版本确定性验证记录齐备", refs, [], "medium")
    return Decision(candidate.candidate_id, "STATIC_ONLY", "源码与语义证据支持候选，独立复核或确定性验证尚未齐备", refs, ["blind_verification and reviewed deterministic evidence"], "medium")

