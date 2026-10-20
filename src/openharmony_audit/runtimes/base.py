"""Runtime protocol shared by Claude Code and OpenAI-compatible backends."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Iterator, Mapping, Protocol


@dataclass(frozen=True)
class RuntimeConfig:
    model: str
    command: str = "claude"
    base_url: str = ""
    api_key_env: str = "OPENAI_API_KEY"
    timeout_seconds: int = 4200
    extra_args: tuple[str, ...] = ()


@dataclass
class AgentEvent:
    event: str
    text: str = ""
    data: Dict[str, Any] = field(default_factory=dict)


class AgentRuntime(Protocol):
    def run(self, prompt: str, *, workdir: str, metadata: Mapping[str, Any] | None = None) -> Iterable[AgentEvent]:
        ...

