"""Declarative responsibilities for the role-based audit workflow."""

from __future__ import annotations

from typing import Dict, List


ROLE_DEFINITIONS: Dict[str, Dict[str, object]] = {
    "entrypoint-boundary": {"stage": "semantic-audit", "outputs": ["entrypoints", "trust_boundaries"]},
    "dataflow-lifetime": {"stage": "semantic-audit", "outputs": ["dataflow", "lifetime_invariants"]},
    "counterevidence-history": {"stage": "semantic-audit", "outputs": ["counter_evidence", "history_refs"]},
    "chain-composer": {"stage": "semantic-audit", "outputs": ["call_chain", "invariant"]},
    "blind-verifier": {"stage": "decision", "outputs": ["independent_reconstruction"]},
    "poc-planner": {"stage": "reporting", "outputs": ["poc_plan", "reproduction_conditions"]},
    "reporter": {"stage": "reporting", "outputs": ["markdown_report", "pdf_report"]},
}


def role_names() -> List[str]:
    """Return a stable ordering for prompt dispatch and plan serialization."""
    return list(ROLE_DEFINITIONS)
