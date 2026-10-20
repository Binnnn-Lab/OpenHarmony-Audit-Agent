"""Deterministic campaign planner built on the original audit workflow ideas."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping

from openharmony_audit.contracts.models import AuditCampaign


DEFAULT_PHASES = [
    {"id": "inventory", "minutes": 30, "objective": "freeze target and threat model"},
    {"id": "discovery", "minutes": 60, "objective": "normalise static findings"},
    {"id": "semantic-audit", "minutes": 90, "objective": "build invariant and counterevidence"},
    {"id": "evidence", "minutes": 120, "objective": "enrich with CodeQL-AI evidence"},
    {"id": "decision", "minutes": 30, "objective": "blind review and report routing"},
]


def load_target_profile(path: str | Path) -> AuditCampaign:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    source = data.get("source", {})
    return AuditCampaign(
        campaign_id=data.get("campaignId", "openharmony-audit"),
        target_id=data["id"],
        display_name=data["displayName"],
        snapshot_id=data.get("snapshotId", data.get("id", "snapshot")),
        revision=source.get("revision", "abstract-profile"),
        units=list(data.get("units", [])),
        threat_model=dict(data.get("threatModel", {})),
        phases=list(data.get("phases", DEFAULT_PHASES)),
        interfaces=dict(data.get("interfaces", {})),
        evidence_rules=dict(data.get("evidenceRules", {})),
    )


def balanced_units(units: Iterable[Mapping[str, Any]], workers: int = 1) -> List[List[Dict[str, Any]]]:
    unit_list = [dict(item) for item in units]
    workers = max(1, min(workers, len(unit_list) or 1))
    ordered = sorted(unit_list, key=lambda item: (-int(item.get("weight", 1)), item.get("id", "")))
    shards: List[List[Dict[str, Any]]] = [[] for _ in range(workers)]
    weights = [0] * workers
    for unit in ordered:
        index = min(range(workers), key=lambda i: (weights[i], i))
        shards[index].append(unit)
        weights[index] += int(unit.get("weight", 1))
    return shards


def build_plan(campaign: AuditCampaign, *, workers: int = 1, candidate_limit: int = 3) -> Dict[str, Any]:
    shards = balanced_units(campaign.units, workers)
    return {
        "schema": "openharmony-audit-plan-v1",
        "campaign": campaign.to_dict(),
        "candidateLimitPerUnit": candidate_limit,
        "workers": [
            {"id": f"worker-{index}", "units": shard, "roles": [
                "entrypoint-boundary", "dataflow-lifetime", "counterevidence-history",
            ]}
            for index, shard in enumerate(shards, 1)
        ],
    }


def prepare_run(campaign: AuditCampaign, run_root: str | Path, *, workers: int = 1) -> Dict[str, Any]:
    root = Path(run_root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    for name in ("candidates", "evidence", "reports", "workers"):
        (root / name).mkdir(exist_ok=True)
    plan = build_plan(campaign, workers=workers)
    (root / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for worker in plan["workers"]:
        worker_root = root / "workers" / worker["id"]
        worker_root.mkdir(parents=True, exist_ok=True)
        (worker_root / "assignment.json").write_text(json.dumps(worker, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return plan

