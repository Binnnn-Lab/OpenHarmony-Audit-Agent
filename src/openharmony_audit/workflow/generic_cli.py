"""Command line interface for planning and running the generic workflow."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

from .generic_contracts import ConfigError, TargetProfile, WorkflowConfig
from .planner import build_plan, prepare_run
from .runner import run_parallel


def _print(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def _load_plan(run_root: Path) -> Dict[str, Any]:
    path = run_root / "plan.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigError("cannot read plan %s: %s" % (path, exc)) from exc
    if not isinstance(value, dict) or value.get("schema") != "generic-audit-plan-v1":
        raise ConfigError("run root does not contain a generic-audit-plan-v1 plan")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generic Claude Code repository-audit workflow")
    sub = parser.add_subparsers(dest="operation", required=True)
    validate = sub.add_parser("validate", help="validate workflow and target configuration")
    validate.add_argument("--workflow", type=Path, required=True)
    validate.add_argument("--target", type=Path, required=True)
    validate.add_argument("--strict-source", action="store_true")
    plan = sub.add_parser("plan", help="print the deterministic worker plan")
    plan.add_argument("--workflow", type=Path, required=True)
    plan.add_argument("--target", type=Path, required=True)
    prepare = sub.add_parser("prepare", help="materialise worker assignments and prompts")
    prepare.add_argument("--workflow", type=Path, required=True)
    prepare.add_argument("--target", type=Path, required=True)
    prepare.add_argument("--run-root", type=Path, required=True)
    prepare.add_argument("--allow-missing-source", action="store_true")
    run = sub.add_parser("run", help="run prepared root workers in parallel")
    run.add_argument("--run-root", type=Path, required=True)
    run.add_argument("--workers", help="comma-separated worker ids")
    status = sub.add_parser("status", help="show persisted worker states")
    status.add_argument("--run-root", type=Path, required=True)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.operation in {"validate", "plan", "prepare"}:
            workflow = WorkflowConfig.load(args.workflow)
            target = TargetProfile.load(args.target)
        if args.operation == "validate":
            workflow.validate_runtime_assets()
            from .generic_adapters import source_adapter

            source_adapter(target).validate(strict=args.strict_source)
            _print({"status": "VALID", "campaignId": workflow.campaign_id, "target": target.id})
        elif args.operation == "plan":
            _print(build_plan(workflow, target))
        elif args.operation == "prepare":
            _print(
                prepare_run(
                    workflow,
                    target,
                    args.run_root,
                    strict_source=not args.allow_missing_source,
                )
            )
        elif args.operation == "run":
            run_root = args.run_root.resolve()
            plan = _load_plan(run_root)
            selected = args.workers.split(",") if args.workers else None
            result = run_parallel(plan, run_root, selected)
            (run_root / "run-result.json").write_text(
                json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            _print(result)
        else:
            run_root = args.run_root.resolve()
            plan = _load_plan(run_root)
            states = []
            for worker in plan["workers"]:
                path = run_root / "workers" / worker["id"] / "worker-state.json"
                if path.is_file():
                    state = json.loads(path.read_text(encoding="utf-8"))
                else:
                    state = {"state": "NOT_STARTED", "terminal": False}
                states.append({"worker": worker["id"], "status": state})
            _print({"campaignId": plan["campaignId"], "workers": states})
        return 0
    except (ConfigError, OSError, ValueError) as exc:
        print("audit-workflow: %s" % exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

