"""Model runtime adapters with one structured event contract."""

from .base import AgentEvent, AgentRuntime, RuntimeConfig
from .claude_code import ClaudeCodeRuntime
from .openai_compatible import OpenAICompatibleRuntime

__all__ = ["AgentEvent", "AgentRuntime", "RuntimeConfig", "ClaudeCodeRuntime", "OpenAICompatibleRuntime"]

