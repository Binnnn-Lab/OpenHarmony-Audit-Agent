"""Atomic checkpoint persistence for resumable campaigns."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict


def write_checkpoint(path: str | Path, state: Dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, target)


def read_checkpoint(path: str | Path) -> Dict[str, Any]:
    target = Path(path)
    if not target.is_file():
        return {"state": "NOT_STARTED", "terminal": False}
    value = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("checkpoint must contain a JSON object")
    return value

