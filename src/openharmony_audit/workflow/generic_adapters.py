"""Source adapter interface and built-in repository/decompiler adapters."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any, Dict, Mapping, Protocol, Tuple

from .generic_contracts import AnalysisUnit, ConfigError, TargetProfile


class SourceAdapter(Protocol):
    """Interface implemented by every source representation."""

    def validate(self, strict: bool = False) -> None:
        """Validate configuration and, in strict mode, local source availability."""

    def units(self) -> Tuple[AnalysisUnit, ...]:
        """Return independent source shards for root workers."""

    def agent_context(self) -> Mapping[str, Any]:
        """Return source facts that may be disclosed to an analysis agent."""


def _discover_units(root: Path) -> Tuple[AnalysisUnit, ...]:
    directories = []
    if root.is_dir():
        directories = sorted(
            item for item in root.iterdir() if item.is_dir() and not item.name.startswith(".")
        )
    if not directories:
        return (AnalysisUnit(id="root", path="."),)
    units = []
    for index, item in enumerate(directories, 1):
        identifier = re.sub(r"[^A-Za-z0-9._-]+", "_", item.name).strip("._-")
        units.append(AnalysisUnit(id=(identifier or "unit-%d" % index)[:128], path=item.name))
    return tuple(units)


@dataclass
class DirectoryAdapter:
    profile: TargetProfile

    def validate(self, strict: bool = False) -> None:
        if strict and not self.profile.source_root.is_dir():
            raise ConfigError("source root does not exist: %s" % self.profile.source_root)
        if strict:
            for unit in self.profile.units:
                if not (self.profile.source_root / unit.path).exists():
                    raise ConfigError(
                        "analysis unit path does not exist: %s" % (self.profile.source_root / unit.path)
                    )

    def units(self) -> Tuple[AnalysisUnit, ...]:
        return self.profile.units or _discover_units(self.profile.source_root)

    def agent_context(self) -> Mapping[str, Any]:
        source = dict(self.profile.interfaces["source"])
        source.update(
            {
                "capabilities": ["read-source", "search-symbols"],
                "historyAvailable": self.profile.interfaces["history"].get("adapter") != "none",
            }
        )
        return source


@dataclass
class GitRepositoryAdapter(DirectoryAdapter):
    def validate(self, strict: bool = False) -> None:
        super().validate(strict=strict)
        if strict and not (self.profile.source_root / ".git").exists():
            raise ConfigError("git-repository source has no .git metadata: %s" % self.profile.source_root)

    def agent_context(self) -> Mapping[str, Any]:
        source = dict(self.profile.interfaces["source"])
        source.update(
            {
                "capabilities": ["read-source", "search-symbols", "read-git-history"],
                "historyAvailable": self.profile.interfaces["history"].get("adapter") != "none",
            }
        )
        return source


@dataclass
class DecompiledTreeAdapter(DirectoryAdapter):
    def agent_context(self) -> Mapping[str, Any]:
        source = dict(self.profile.interfaces["source"])
        source.update(
            {
                "capabilities": [
                    "read-pseudocode",
                    "search-symbols",
                    "read-address-map",
                    "read-callgraph",
                ],
                "historyAvailable": False,
                "evidenceCaveat": (
                    "pseudocode types, names, control flow and ownership are hypotheses until "
                    "supported by disassembly, xrefs, data layout, or runtime evidence"
                ),
            }
        )
        return source


def source_adapter(profile: TargetProfile) -> SourceAdapter:
    adapters: Dict[str, Any] = {
        "git-repository": GitRepositoryAdapter,
        "directory-tree": DirectoryAdapter,
        "decompiled-tree": DecompiledTreeAdapter,
    }
    return adapters[profile.source_kind](profile)

