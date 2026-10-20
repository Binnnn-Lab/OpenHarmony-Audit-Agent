"""Small schema checks used by the CLI without requiring a validation package."""

from __future__ import annotations

from typing import Any, Mapping

from .evidence import DECISION_VERDICTS, EVIDENCE_KINDS


def validate_finding(value: Mapping[str, Any]) -> None:
    required = ("finding_id", "engine", "rule_id", "file_path", "start_line")
    missing = [name for name in required if not value.get(name)]
    if missing:
        raise ValueError("finding missing fields: " + ", ".join(missing))
    if not isinstance(value["start_line"], int) or value["start_line"] < 1:
        raise ValueError("finding.start_line must be a positive integer")


def validate_evidence(value: Mapping[str, Any]) -> None:
    for name in ("evidence_id", "kind", "producer", "created_at", "content_hash"):
        if not value.get(name):
            raise ValueError("evidence missing field: " + name)
    if value["kind"] not in EVIDENCE_KINDS:
        raise ValueError("unknown evidence kind: " + str(value["kind"]))


def validate_decision(value: Mapping[str, Any]) -> None:
    if value.get("verdict") not in DECISION_VERDICTS:
        raise ValueError("unknown decision verdict")

