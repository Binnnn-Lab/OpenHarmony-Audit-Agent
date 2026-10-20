"""Command line entrypoint for planning and reporting."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from openharmony_audit.evidence.normalizer import findings_from_sarif
from openharmony_audit.reporting.markdown_report import build_markdown_report
from openharmony_audit.reporting.pdf_report import build_pdf
from openharmony_audit.workflow.planner import load_target_profile, prepare_run


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "workflow":
        from openharmony_audit.workflow.generic_cli import main as workflow_main
        return workflow_main(argv[1:])
    parser = argparse.ArgumentParser(description="OpenHarmony-Audit-Agent")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("workflow", help="primary audit workflow: validate, plan, prepare, run, status")
    validate = sub.add_parser("validate-target")
    validate.add_argument("--target", type=Path, required=True)
    plan = sub.add_parser("prepare")
    plan.add_argument("--target", type=Path, required=True)
    plan.add_argument("--run-root", type=Path, required=True)
    plan.add_argument("--workers", type=int, default=1)
    normalise = sub.add_parser("normalize-sarif")
    normalise.add_argument("--sarif", type=Path, required=True)
    normalise.add_argument("--output", type=Path, required=True)
    report = sub.add_parser("report")
    report.add_argument("--output", type=Path, default=Path("reports/technical-report.md"))
    report.add_argument("--pdf", type=Path, default=Path("reports/technical-report.pdf"))
    args = parser.parse_args(argv)
    if args.command == "validate-target":
        campaign = load_target_profile(args.target)
        print(json.dumps(campaign.to_dict(), ensure_ascii=False, indent=2))
    elif args.command == "prepare":
        campaign = load_target_profile(args.target)
        print(json.dumps(prepare_run(campaign, args.run_root, workers=args.workers), ensure_ascii=False, indent=2))
    elif args.command == "normalize-sarif":
        findings = [item.to_dict() for item in findings_from_sarif(args.sarif)]
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(findings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"normalised {len(findings)} findings")
    elif args.command == "report":
        campaign = {"target": {"id": "openharmony-abstract", "displayName": "OpenHarmony abstract target"}}
        markdown = build_markdown_report(args.output, campaign=campaign)
        build_pdf(markdown, args.pdf)
        print(json.dumps({"markdown": str(markdown), "pdf": str(args.pdf)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

