"""Stable evidence-provider facade for CodeQL-AI capabilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from openharmony_audit.engines.codeql_ai._legacy.lib_fp_experience import (
    analyze_fp_report,
    match_experience_to_ql,
    read_source_context,
    save_fp_experience,
)
from openharmony_audit.engines.codeql_ai._legacy.lib_knowledge import load_applicable_experiences
from openharmony_audit.engines.codeql_ai._legacy.lib_ql_optimizer import inspect_ql_query, inspect_source_code, write_ql_query
from openharmony_audit.engines.codeql_ai._legacy.lib_sanitizer import patch_ql, read_function_implementation, run_taint_analysis
class CodeQLAIProviders:
    """All four CodeQL-AI families under one orchestration-facing API."""

    def __init__(self, knowledge_base_path: Optional[str] = None):
        self.knowledge_base_path = knowledge_base_path

    def match_fp_experience(self, ql_file_path: str, **filters: Any) -> Dict[str, Any]:
        filters["include_global"] = filters.get("include_global", True)
        if self.knowledge_base_path:
            filters["knowledge_base_path"] = self.knowledge_base_path
        loaded = load_applicable_experiences(**filters)
        matches = []
        for experience in loaded.get("experiences", []):
            result = match_experience_to_ql(experience, ql_file_path)
            matches.append({"experience": experience, "match": result})
        matches.sort(key=lambda item: item["match"].get("score", 0), reverse=True)
        return {"success": True, "count": len(matches), "matches": matches}

    def inspect_ql(self, path: str) -> Dict[str, Any]:
        return inspect_ql_query(path)

    def inspect_source(self, path: str) -> Dict[str, Any]:
        return inspect_source_code(path)

    def patch_query(self, name: str, content: str, original: str = "") -> Dict[str, Any]:
        return write_ql_query(name, content, original)

    async def find_sanitizers(self, taint: Dict[str, Any], database: str) -> Any:
        return await run_taint_analysis(taint, database)

    def read_function(self, function_name: str, file_path: str) -> Dict[str, Any]:
        return read_function_implementation(function_name, file_path)

    def parse_paths(self, sarif: str, dataset_root: str, output_dir: Optional[str] = None) -> Dict[str, Any]:
        from openharmony_audit.engines.codeql_ai._legacy.symbolic_sanitizer import parse_sarif

        return parse_sarif(sarif, dataset_root, output_dir=output_dir)

    def symbolic_verify(self, **kwargs: Any) -> Dict[str, Any]:
        from openharmony_audit.engines.codeql_ai._legacy.symbolic_sanitizer import verify_with_decisions

        return verify_with_decisions(**kwargs)

    def symbolic_build(self, source_file: str, source_api: str, compile_script: str, dataset_path: Optional[str] = None) -> Dict[str, Any]:
        from openharmony_audit.engines.codeql_ai._legacy.symbolic_sanitizer import build_binary

        return build_binary(source_file, source_api, compile_script, dataset_path=dataset_path)

    def symbolic_scan(self, binary_path: str, path: Dict[str, Any], source_mode: str, timeout: int = 120) -> Dict[str, Any]:
        from openharmony_audit.engines.codeql_ai._legacy.symbolic_sanitizer import scan_path_branches

        return scan_path_branches(binary_path, path, source_mode, timeout=timeout)

    def compile_config(self, dataset_path: str) -> Dict[str, Any]:
        from openharmony_audit.engines.codeql_ai._legacy.symbolic_sanitizer import resolve_compile_config

        return resolve_compile_config(dataset_path)

