"""Small MCP server exposing the same provider contract used by the CLI."""

from __future__ import annotations

from typing import Any, Dict

from openharmony_audit.engines.codeql_ai.providers import CodeQLAIProviders


def create_server():
    try:
        from fastmcp import FastMCP
    except ImportError as exc:  # pragma: no cover - optional runtime dependency
        raise RuntimeError("install fastmcp to expose MCP tools") from exc
    providers = CodeQLAIProviders()
    server = FastMCP(name="openharmony-audit-agent")

    @server.tool()
    def match_fp_experience(ql_file_path: str, repo_id: str | None = None, cwe: str | None = None) -> Dict[str, Any]:
        return providers.match_fp_experience(ql_file_path, repo_id=repo_id, cwe=cwe, experience_type="false_positive")

    @server.tool()
    def inspect_ql(path: str) -> Dict[str, Any]:
        return providers.inspect_ql(path)

    @server.tool()
    def inspect_source(path: str) -> Dict[str, Any]:
        return providers.inspect_source(path)

    return server

