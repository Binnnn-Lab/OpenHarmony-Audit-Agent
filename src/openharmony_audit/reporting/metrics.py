"""Metric schema without inventing benchmark values."""

from __future__ import annotations

from collections import Counter
from typing import Any, Iterable, Mapping


def summarise_decisions(decisions: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    counts = Counter(str(item.get("verdict", "UNKNOWN")) for item in decisions)
    return {"count": sum(counts.values()), "byVerdict": dict(sorted(counts.items()))}

