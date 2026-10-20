"""Stage scheduler that records deterministic hand-offs between agents and engines."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List


@dataclass
class StageEvent:
    stage: str
    status: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AuditScheduler:
    """A small orchestration core; external runtimes plug into each stage."""

    STAGES = ("inventory", "discovery", "semantic-audit", "evidence", "decision", "reporting")

    def __init__(self) -> None:
        self.events: List[StageEvent] = []

    def start(self, stage: str, **details: Any) -> StageEvent:
        if stage not in self.STAGES:
            raise ValueError("unknown audit stage: " + stage)
        event = StageEvent(stage, "started", details)
        self.events.append(event)
        return event

    def finish(self, stage: str, status: str = "completed", **details: Any) -> StageEvent:
        event = StageEvent(stage, status, details)
        self.events.append(event)
        return event

    def to_dict(self) -> List[Dict[str, Any]]:
        return [{"stage": item.stage, "status": item.status, "details": item.details, "timestamp": item.timestamp} for item in self.events]

