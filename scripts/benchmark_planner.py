"""Synthetic planning overhead only; does not read or audit source files."""
import argparse
import hashlib
import json
import time
from pathlib import Path

from openharmony_audit.workflow.generic_contracts import AnalysisUnit, TargetProfile, WorkflowConfig
from openharmony_audit.workflow.generic_planner import build_plan


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--units", type=int, required=True)
    parser.add_argument("--iterations", type=int, default=20)
    parser.add_argument("--workflow", type=Path, default=Path("config/workflow.audit.example.json"))
    args = parser.parse_args()
    if min(args.units, args.iterations) < 1:
        parser.error("units and iterations must be positive")
    workflow = WorkflowConfig.load(args.workflow)
    units = tuple(AnalysisUnit("unit-%06d" % i, "synthetic/unit-%06d" % i, ("abstract",), i % 7 + 1) for i in range(args.units))
    target = TargetProfile("synthetic-planner", "Synthetic metadata", "directory-tree", Path.cwd(),
                           "synthetic-v1", units,
                           {"source": {"adapter": "directory-tree"}, "history": {"adapter": "none"}},
                           {}, {}, Path("synthetic-profile.json"))
    start = time.perf_counter()
    for _ in range(args.iterations):
        plan = build_plan(workflow, target)
    elapsed = time.perf_counter() - start
    count = sum(len(worker["units"]) for worker in plan["workers"])
    assert count == args.units
    print(json.dumps({"scope": "synthetic-planner-only", "units": args.units, "iterations": args.iterations,
                      "workers": len(plan["workers"]), "planning_seconds": elapsed,
                      "seconds_per_plan": elapsed / args.iterations,
                      "input_spec_sha256": hashlib.sha256(f"synthetic-v1:{args.units}:weight=i%7+1".encode()).hexdigest(),
                      "source_files_scanned": 0, "model_calls": 0, "codeql_calls": 0}))


if __name__ == "__main__":
    main()
