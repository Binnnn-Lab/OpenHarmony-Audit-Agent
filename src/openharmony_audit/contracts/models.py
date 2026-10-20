"""Dependency-free, serialisable contracts for the unified audit pipeline."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Optional


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _dict(value: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    return dict(value or {})


@dataclass
class Evidence:
    """An auditable fact produced by one deterministic or model-backed step."""

    evidence_id: str
    kind: str
    producer: str
    status: str = "available"
    candidate_id: Optional[str] = None
    source_ref: Optional[str] = None
    input_hash: Optional[str] = None
    content_hash: Optional[str] = None
    rule_version: Optional[str] = None
    model_version: Optional[str] = None
    content: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if not self.content_hash:
            payload = json.dumps(self.content, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
            self.content_hash = hashlib.sha256(payload).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Finding:
    """Normalised static-analysis result, preserving SARIF provenance."""

    finding_id: str
    engine: str
    rule_id: str
    message: str
    file_path: str
    start_line: int
    end_line: Optional[int] = None
    cwe: Optional[str] = None
    cve: Optional[str] = None
    source: Dict[str, Any] = field(default_factory=dict)
    sink: Dict[str, Any] = field(default_factory=dict)
    code_flow: List[Dict[str, Any]] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)
    provenance: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CandidatePacket:
    """Frozen candidate passed between discovery, verification and reporting."""

    candidate_id: str
    revision: int
    snapshot_id: str
    unit_id: str
    title: str
    locations: Dict[str, Dict[str, Any]]
    call_chain: List[Dict[str, Any]]
    invariant: Dict[str, Any]
    threat_model: Dict[str, Any]
    impact: Dict[str, Any]
    counter_evidence: List[Dict[str, Any]] = field(default_factory=list)
    evidence_refs: List[str] = field(default_factory=list)
    unresolved_assumptions: List[str] = field(default_factory=list)
    finding_ids: List[str] = field(default_factory=list)
    cwe: Optional[str] = None
    cve: Optional[str] = None
    poc_plan: Dict[str, Any] = field(default_factory=dict)
    repair_plan: Dict[str, Any] = field(default_factory=dict)
    provenance: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        value = asdict(self)
        value["schema"] = "audit-candidate-packet-v1"
        return value


@dataclass
class Decision:
    candidate_id: str
    verdict: str
    rationale: str
    evidence_refs: List[str] = field(default_factory=list)
    missing_evidence: List[str] = field(default_factory=list)
    confidence: str = "low"
    reviewer: str = "decision-gate"
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ExperienceRecord:
    experience_id: str
    experience_type: str
    repo_id: str
    language: str
    cwe: Optional[str]
    pattern_summary: str
    root_cause: str
    confidence: str = "low"
    status: str = "candidate"
    validation: Dict[str, Any] = field(default_factory=dict)
    evidence_refs: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AuditCampaign:
    campaign_id: str
    target_id: str
    display_name: str
    snapshot_id: str
    revision: str
    units: List[Dict[str, Any]]
    threat_model: Dict[str, Any]
    phases: List[Dict[str, Any]]
    interfaces: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    evidence_rules: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        value = asdict(self)
        value["schema"] = "audit-campaign-v1"
        return value

