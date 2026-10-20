"""Bridge to the embedded CodeQL-AI experience store."""

from __future__ import annotations

from typing import Any, Dict, Optional

from openharmony_audit.engines.codeql_ai._legacy.lib_knowledge import (
    load_applicable_experiences,
    save_experience_pattern,
    update_experience_validation,
)


class ExperienceStore:
    """Expose one stable interface while retaining CodeQL-AI JSONL semantics."""

    def __init__(self, knowledge_base_path: Optional[str] = None):
        self.knowledge_base_path = knowledge_base_path

    def load(self, **filters: Any) -> Dict[str, Any]:
        filters["knowledge_base_path"] = self.knowledge_base_path
        return load_applicable_experiences(**filters)

    def save(self, **pattern: Any) -> Dict[str, Any]:
        pattern["knowledge_base_path"] = self.knowledge_base_path
        return save_experience_pattern(pattern, knowledge_base_path=self.knowledge_base_path)

    def validate(self, experience_id: str, **updates: Any) -> Dict[str, Any]:
        updates["knowledge_base_path"] = self.knowledge_base_path
        return update_experience_validation(experience_id, **updates)

