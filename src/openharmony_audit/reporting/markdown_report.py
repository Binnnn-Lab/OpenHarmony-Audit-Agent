"""Render the packaged technical manual; imported records are explicitly separated."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence


def build_markdown_report(output: str | Path, *, campaign: Mapping[str, Any], findings: Sequence[Mapping[str, Any]] = (), decisions: Sequence[Mapping[str, Any]] = ()) -> Path:
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    template = Path(__file__).with_name("technical-report-template.md").read_text(encoding="utf-8")
    if findings or decisions:
        summary = {"findingCount": len(findings), "decisionCount": len(decisions), "decisions": list(decisions)}
        template += "\n## 附录：输入记录统计\n\n统计范围为调用方提供的告警及判定记录。\n\n```json\n" + json.dumps(summary, ensure_ascii=False, indent=2) + "\n```\n"
    target.write_text(template, encoding="utf-8")
    return target
