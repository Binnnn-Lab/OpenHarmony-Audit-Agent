"""Claude Code adapter compatible with the original stream-json runner."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any, Iterable, Mapping

from .base import AgentEvent, RuntimeConfig


class ClaudeCodeRuntime:
    def __init__(self, config: RuntimeConfig):
        self.config = config

    def run(self, prompt: str, *, workdir: str, metadata: Mapping[str, Any] | None = None) -> Iterable[AgentEvent]:
        command = [
            self.config.command, "-p", "--model", self.config.model,
            "--verbose", "--output-format", "stream-json", *self.config.extra_args,
        ]
        process = subprocess.Popen(
            command,
            cwd=str(Path(workdir)),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            env=os.environ.copy(),
        )
        stdout, _ = process.communicate(prompt, timeout=self.config.timeout_seconds)
        last_data: dict[str, Any] = {}
        for line in stdout.splitlines():
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                yield AgentEvent("log", line)
                continue
            last_data = data
            text = data.get("text") or data.get("content") or data.get("message", "")
            yield AgentEvent(str(data.get("type", "event")), str(text), data)
        yield AgentEvent("completed" if process.returncode == 0 else "failed", data={"returncode": process.returncode, "last_event": last_data})

