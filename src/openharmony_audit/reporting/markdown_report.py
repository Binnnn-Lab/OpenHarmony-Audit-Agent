"""Render the packaged technical manual; imported records are explicitly separated."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence


def build_markdown_report(output: str | Path, *, campaign: Mapping[str, Any], findings: Sequence[Mapping[str, Any]] = (), decisions: Sequence[Mapping[str, Any]] = ()) -> Path:
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    template = Path(__file__).with_name("technical-report-template.md").read_text(encoding="utf-8")
    summary = {"findingCount": len(findings), "decisionCount": len(decisions), "decisions": list(decisions)}
    target.write_text(template + "\n## 附录：本次传入的记录摘要\n\n以下仅统计调用方传入数据，不代表已运行扫描。\n\n```json\n" + json.dumps(summary, ensure_ascii=False, indent=2) + "\n```\n", encoding="utf-8")
    return target
