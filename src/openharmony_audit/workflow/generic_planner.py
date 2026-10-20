"""Deterministic sharding and workspace materialisation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

from .generic_adapters import source_adapter
from .generic_contracts import AnalysisUnit, ConfigError, TargetProfile, WorkflowConfig


def _balanced_shards(units: Sequence[AnalysisUnit], count: int) -> List[List[AnalysisUnit]]:
    shards: List[List[AnalysisUnit]] = [[] for _ in range(count)]
    loads = [0 for _ in range(count)]
    for unit in sorted(units, key=lambda item: (-item.weight, item.id)):
        destination = min(range(count), key=lambda index: (loads[index], index))
        shards[destination].append(unit)
        loads[destination] += unit.weight
    return shards


def _one_per_worker(units: Sequence[AnalysisUnit], count: int) -> List[List[AnalysisUnit]]:
    shards: List[List[AnalysisUnit]] = [[] for _ in range(count)]
    for index, unit in enumerate(units):
        shards[index % count].append(unit)
    return shards


def _phase_dicts(workflow: WorkflowConfig) -> List[Dict[str, Any]]:
    return [
        {"id": phase.id, "minutes": phase.minutes, "objective": phase.objective}
        for phase in workflow.phases
    ]


def build_plan(workflow: WorkflowConfig, target: TargetProfile) -> Dict[str, Any]:
    adapter = source_adapter(target)
    adapter.validate(strict=False)
    units = adapter.units()
    if not units:
        raise ConfigError("source adapter returned no analysis units")
    requested = workflow.parallelism.root_workers
    worker_count = min(requested, len(units))
    if workflow.parallelism.shard_strategy == "one-unit-per-worker":
        shards = _one_per_worker(units, worker_count)
    else:
        shards = _balanced_shards(units, worker_count)
    workers = []
    roles = workflow.parallelism.subagent_roles[: workflow.parallelism.subagents_per_worker]
    for index, shard in enumerate(shards, 1):
        workers.append(
            {
                "id": "worker-%d" % index,
                "role": "shard-controller",
                "units": [
                    {
                        "id": unit.id,
                        "path": unit.path,
                        "focus": list(unit.focus),
                        "weight": unit.weight,
                        "metadata": dict(unit.metadata),
                    }
                    for unit in sorted(shard, key=lambda item: item.id)
                ],
                "subagentRoles": list(roles),
                "candidateLimitPerUnit": workflow.candidate_limit_per_unit,
            }
        )
    return {
        "schema": "generic-audit-plan-v1",
        "campaignId": workflow.campaign_id,
        "target": {
            "id": target.id,
            "displayName": target.display_name,
            "profile": str(target.profile_path),
            "source": dict(adapter.agent_context()),
            "interfaces": {name: dict(value) for name, value in target.interfaces.items()},
            "threatModel": dict(target.threat_model),
            "evidenceRules": dict(target.evidence_rules),
        },
        "runtime": {
            "adapter": workflow.runtime.adapter,
            "command": workflow.runtime.command,
            "model": workflow.runtime.model,
            "outputFormat": workflow.runtime.output_format,
            "mainTimeoutSeconds": workflow.runtime.main_timeout_seconds,
            "checkpointTimeoutSeconds": workflow.runtime.checkpoint_timeout_seconds,
            "maxCycles": workflow.runtime.max_cycles,
            "extraArgs": list(workflow.runtime.extra_args),
            "inheritEnv": list(workflow.runtime.inherit_env),
            "env": dict(workflow.runtime.env),
        },
        "parallelism": {
            "rootWorkers": worker_count,
            "requestedRootWorkers": requested,
            "subagentsPerWorker": workflow.parallelism.subagents_per_worker,
            "serializeValidation": workflow.parallelism.serialize_validation,
        },
        "phases": _phase_dicts(workflow),
        "terminalStates": list(workflow.terminal_states),
        "workers": workers,
    }


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _render_worker_prompt(template: str, plan: Mapping[str, Any], worker: Mapping[str, Any]) -> str:
    packet = {
        "campaignId": plan["campaignId"],
        "target": plan["target"],
        "phases": plan["phases"],
        "parallelism": plan["parallelism"],
        "assignment": worker,
        "terminalStates": plan["terminalStates"],
    }
    return (
        template.rstrip()
        + "\n\n## 本次任务包（由规划器生成）\n\n```json\n"
        + json.dumps(packet, ensure_ascii=False, indent=2)
        + "\n```\n"
    )


def prepare_run(
    workflow: WorkflowConfig,
    target: TargetProfile,
    run_root: Path,
    strict_source: bool = True,
) -> Dict[str, Any]:
    workflow.validate_runtime_assets()
    source_adapter(target).validate(strict=strict_source)
    plan = build_plan(workflow, target)
    run_root = run_root.resolve()
    run_root.mkdir(parents=True, exist_ok=True)
    (run_root / "shared" / "candidates").mkdir(parents=True, exist_ok=True)
    (run_root / "shared" / "verification").mkdir(parents=True, exist_ok=True)
    (run_root / "shared" / "reports").mkdir(parents=True, exist_ok=True)
    _write_json(run_root / "plan.json", plan)
    controller = (workflow.prompt_dir / "controller.md").read_text(encoding="utf-8")
    for worker in plan["workers"]:
        worker_root = run_root / "workers" / worker["id"]
        worker_root.mkdir(parents=True, exist_ok=True)
        (worker_root / "home").mkdir(exist_ok=True)
        candidate_root = run_root / "shared" / "candidates" / worker["id"]
        verification_root = run_root / "shared" / "verification" / worker["id"]
        report_root = run_root / "shared" / "reports" / worker["id"]
        candidate_root.mkdir(parents=True, exist_ok=True)
        verification_root.mkdir(parents=True, exist_ok=True)
        report_root.mkdir(parents=True, exist_ok=True)
        assignment = {
            "schema": "generic-audit-worker-assignment-v1",
            "campaignId": plan["campaignId"],
            "target": plan["target"],
            "phases": plan["phases"],
            "parallelism": plan["parallelism"],
            "assignment": worker,
            "paths": {
                "workerRoot": str(worker_root),
                "sharedRoot": str(run_root / "shared"),
                "candidateRoot": str(candidate_root),
                "verificationRoot": str(verification_root),
                "reportRoot": str(report_root),
                "state": str(worker_root / "worker-state.json"),
                "checkpoint": str(worker_root / "checkpoint.json"),
                "home": str(worker_root / "home"),
            },
        }
        _write_json(worker_root / "assignment.json", assignment)
        (worker_root / "prompt.md").write_text(
            _render_worker_prompt(controller, plan, worker), encoding="utf-8"
        )
        (worker_root / "blind-verifier.md").write_text(
            (workflow.prompt_dir / "blind-verifier.md").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        (worker_root / "roles.md").write_text(
            (workflow.prompt_dir / "roles.md").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        (worker_root / "checkpoint-prompt.md").write_text(
            (workflow.prompt_dir / "checkpoint.md").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
    return plan

