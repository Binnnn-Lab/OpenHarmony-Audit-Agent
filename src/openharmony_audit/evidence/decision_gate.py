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
    items = list(evidence)
    kinds = {str(item.get("kind")) for item in items if item.get("status", "available") == "available"}
    refs = [str(item.get("evidence_id")) for item in items if item.get("evidence_id")]
    if "static_path" not in kinds and "sarif_alert" not in kinds:
        return Decision(candidate.candidate_id, "NEEDS_EVIDENCE", "缺少静态路径或 SARIF 告警证据", refs, ["static_path"], "low")
    if not candidate.invariant or not candidate.threat_model:
        return Decision(candidate.candidate_id, "NEEDS_EVIDENCE", "漏洞不变量或威胁边界不完整", refs, ["invariant", "threat_model"], "low")
    if len(candidate.counter_evidence) < 2:
        return Decision(candidate.candidate_id, "NEEDS_EVIDENCE", "尚未完成至少两条反证检查", refs, ["counter_evidence"], "low")
    deterministic = {"symbolic_reachability", "poc_execution", "deterministic_verification"}
    if kinds.intersection(deterministic):
        return Decision(candidate.candidate_id, "CONFIRMED", "静态路径、漏洞不变量、反证与确定性复核证据齐备", refs, [], "medium")
    return Decision(candidate.candidate_id, "STATIC_ONLY", "静态与语义证据齐备，但尚无确定性动态复核", refs, ["symbolic_reachability or executable_poc"], "medium")

