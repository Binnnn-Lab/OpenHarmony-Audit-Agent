"""CodeQL command adapter and SARIF hand-off."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List

from openharmony_audit.evidence.normalizer import findings_from_sarif


@dataclass(frozen=True)
class CodeQLConfig:
    cli: str = "codeql"
    language: str = "cpp"
    query_suite: str = "cpp-security-and-quality.qls"
    timeout_seconds: int = 3600


def run_codeql_analysis(
    database: str | Path,
    output_sarif: str | Path,
    *,
    config: CodeQLConfig | None = None,
    queries: str | Path | None = None,
) -> Dict[str, Any]:
    """Run CodeQL when explicitly requested and return normalised findings."""
    cfg = config or CodeQLConfig()
    query = str(queries or cfg.query_suite)
    command = [cfg.cli, "database", "analyze", str(database), query, "--format=sarif-latest", "--output", str(output_sarif)]
    completed = subprocess.run(command, capture_output=True, text=True, timeout=cfg.timeout_seconds, check=False)
    result: Dict[str, Any] = {
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "sarif": str(output_sarif),
    }
    if completed.returncode == 0 and Path(output_sarif).is_file():
        findings = findings_from_sarif(output_sarif)
        result["findings"] = [finding.to_dict() for finding in findings]
        result["count"] = len(findings)
    else:
        result["findings"] = []
        result["count"] = 0
    return result

