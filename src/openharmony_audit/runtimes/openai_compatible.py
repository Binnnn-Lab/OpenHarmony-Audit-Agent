"""OpenAI-compatible streaming chat adapter using only the standard library."""

from __future__ import annotations

import json
import os
from typing import Any, Iterable, Mapping
from urllib import request

from .base import AgentEvent, RuntimeConfig


class OpenAICompatibleRuntime:
    def __init__(self, config: RuntimeConfig):
        if not config.base_url:
            raise ValueError("base_url is required for OpenAI-compatible runtime")
        self.config = config

    def run(self, prompt: str, *, workdir: str, metadata: Mapping[str, Any] | None = None) -> Iterable[AgentEvent]:
        key = os.environ.get(self.config.api_key_env, "")
        payload = {
            "model": self.config.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": True,
        }
        base_url = self.config.base_url.rstrip("/")
        endpoint = base_url + ("/chat/completions" if base_url.endswith("/v1") else "/v1/chat/completions")
        req = request.Request(endpoint, data=json.dumps(payload).encode("utf-8"), method="POST")
        req.add_header("Content-Type", "application/json")
        if key:
            req.add_header("Authorization", "Bearer " + key)
        with request.urlopen(req, timeout=self.config.timeout_seconds) as response:
            for raw in response:
                line = raw.decode("utf-8", errors="replace").strip()
                if not line or line.startswith(":"):
                    continue
                if line.startswith("data:"):
                    line = line[5:].strip()
                if line == "[DONE]":
                    yield AgentEvent("completed")
                    return
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    yield AgentEvent("log", line)
                    continue
                choices = data.get("choices", [])
                delta = choices[0].get("delta", {}) if choices else {}
                text = delta.get("content", "")
                yield AgentEvent("delta", text, data)
        yield AgentEvent("completed")

