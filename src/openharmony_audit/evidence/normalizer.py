"""Convert SARIF results into the unified Finding contract."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional

from openharmony_audit.contracts.models import Finding


def _location(location: Mapping[str, Any]) -> Dict[str, Any]:
    physical = location.get("physicalLocation", location)
    artifact = physical.get("artifactLocation", {})
    region = physical.get("region", {})
    return {
        "path": artifact.get("uri") or artifact.get("uriBaseId") or "",
        "startLine": int(region.get("startLine", 1) or 1),
        "endLine": region.get("endLine"),
        "startColumn": region.get("startColumn"),
        "endColumn": region.get("endColumn"),
    }


def _cwe(result: Mapping[str, Any], rule: Mapping[str, Any]) -> Optional[str]:
    values = [result.get("properties", {}).get("cwe"), rule.get("properties", {}).get("cwe")]
    for value in values:
        if value:
            text = str(value).upper()
            return text if text.startswith("CWE-") else "CWE-" + text.removeprefix("CWE")
    rule_id = str(result.get("ruleId", ""))
    if "cwe-" in rule_id.lower():
        tail = rule_id.lower().split("cwe-", 1)[1].split("/", 1)[0]
        if tail.isdigit():
            return "CWE-" + tail
    return None


def _flow(result: Mapping[str, Any]) -> List[Dict[str, Any]]:
    flow: List[Dict[str, Any]] = []
    for code_flow in result.get("codeFlows", []) or []:
        for thread in code_flow.get("threadFlows", []) or []:
            for item in thread.get("locations", []) or []:
                loc = item.get("location", {})
                flow.append({
                    "location": _location(loc),
                    "message": (loc.get("message") or {}).get("text", ""),
                })
    return flow


def findings_from_sarif(path: str | Path, *, engine: str = "codeql") -> List[Finding]:
    """Read SARIF 2.1.0 and preserve enough detail for later evidence."""
    source = Path(path)
    raw = source.read_bytes()
    data = json.loads(raw.decode("utf-8"))
    digest = hashlib.sha256(raw).hexdigest()
    findings: List[Finding] = []
    for run in data.get("runs", []) or []:
        tool = (run.get("tool", {}).get("driver", {}) or {})
        rules = {str(item.get("id")): item for item in tool.get("rules", []) or []}
        for index, result in enumerate(run.get("results", []) or []):
            primary = (result.get("locations") or [{}])[0]
            location = _location(primary.get("location", {}))
            result_id = result.get("guid") or result.get("id") or f"{index:05d}"
            rule_id = str(result.get("ruleId") or "unknown-rule")
            findings.append(Finding(
                finding_id=f"{engine}:{result_id}",
                engine=engine,
                rule_id=rule_id,
                message=(result.get("message") or {}).get("text", ""),
                file_path=location["path"],
                start_line=location["startLine"],
                end_line=location.get("endLine"),
                cwe=_cwe(result, rules.get(rule_id, {})),
                cve=result.get("properties", {}).get("cve"),
                source=result.get("properties", {}).get("source", {}),
                sink=result.get("properties", {}).get("sink", {}),
                code_flow=_flow(result),
                properties=dict(result.get("properties", {}) or {}),
                provenance={"sarif": str(source), "sha256": digest, "runTool": tool.get("name", engine)},
            ))
    return findings

