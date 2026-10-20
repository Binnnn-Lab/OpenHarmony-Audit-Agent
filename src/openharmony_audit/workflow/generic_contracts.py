"""Small, dependency-free contracts for the generic agent workflow."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence, Tuple


_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
INTERFACE_NAMES = (
    "source",
    "history",
    "index",
    "seeds",
    "domain",
    "staticAnalysis",
    "validation",
    "capability",
    "novelty",
    "artifactStore",
    "reporting",
)
DEFAULT_PHASES = (
    ("inventory", 30),
    ("discovery", 60),
    ("verification", 120),
    ("decision", 30),
)
DEFAULT_SUBAGENT_ROLES = (
    "entrypoint-boundary",
    "dataflow-lifetime",
    "counterevidence-history",
)


class ConfigError(ValueError):
    """A workflow or target profile is incomplete or inconsistent."""


def _object(value: Any, name: str) -> Dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ConfigError(name + " must be a JSON object")
    return dict(value)


def _text(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(name + " must be a non-empty string")
    return value.strip()


def _identifier(value: Any, name: str) -> str:
    result = _text(value, name)
    if not _ID_RE.fullmatch(result):
        raise ConfigError(name + " contains unsupported characters")
    return result


def _positive_int(value: Any, name: str, maximum: int = 86400) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1 or value > maximum:
        raise ConfigError("%s must be an integer from 1 through %d" % (name, maximum))
    return value


def _string_tuple(value: Any, name: str) -> Tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ConfigError(name + " must be an array of strings")
    result = tuple(_text(item, name + "[]") for item in value)
    if len(set(result)) != len(result):
        raise ConfigError(name + " contains duplicates")
    return result


def _load_json(path: Path) -> Dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigError("cannot read JSON from %s: %s" % (path, exc)) from exc
    return _object(value, str(path))


def _safe_relative_path(value: Any, name: str) -> str:
    text = _text(value, name).replace("\\", "/")
    path = Path(text)
    if path.is_absolute() or ".." in path.parts:
        raise ConfigError(name + " must be a relative path below the source root")
    return path.as_posix()


@dataclass(frozen=True)
class Phase:
    id: str
    minutes: int
    objective: str = ""

    @classmethod
    def from_dict(cls, value: Mapping[str, Any], index: int) -> "Phase":
        data = _object(value, "phases[%d]" % index)
        inherit_env = _string_tuple(data.get("inheritEnv", ()), "runtime.inheritEnv")
        if any(re.fullmatch(r"[A-Z_][A-Z0-9_]*", name) is None for name in inherit_env):
            raise ConfigError("runtime.inheritEnv contains an invalid variable name")
        return cls(
            id=_identifier(data.get("id"), "phases[%d].id" % index),
            minutes=_positive_int(data.get("minutes"), "phases[%d].minutes" % index, 10080),
            objective=str(data.get("objective", "")).strip(),
        )


@dataclass(frozen=True)
class RuntimeConfig:
    adapter: str
    command: str
    model: str
    output_format: str = "stream-json"
    main_timeout_seconds: int = 4200
    checkpoint_timeout_seconds: int = 300
    max_cycles: int = 1
    extra_args: Tuple[str, ...] = ()
    inherit_env: Tuple[str, ...] = ()
    env: Mapping[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "RuntimeConfig":
        data = _object(value, "runtime")
        adapter = _identifier(data.get("adapter", "claude-code"), "runtime.adapter")
        if adapter != "claude-code":
            raise ConfigError("runtime.adapter must currently be claude-code")
        raw_env = _object(data.get("env", {}), "runtime.env")
        env: Dict[str, str] = {}
        for key, item in raw_env.items():
            if not isinstance(key, str) or not re.fullmatch(r"[A-Z_][A-Z0-9_]*", key):
                raise ConfigError("runtime.env contains an invalid variable name")
            env[key] = _text(item, "runtime.env.%s" % key)
        inherit_env = _string_tuple(data.get("inheritEnv", ()), "runtime.inheritEnv")
        if any(re.fullmatch(r"[A-Z_][A-Z0-9_]*", name) is None for name in inherit_env):
            raise ConfigError("runtime.inheritEnv contains an invalid variable name")
        return cls(
            adapter=adapter,
            command=_text(data.get("command", "claude"), "runtime.command"),
            model=_text(data.get("model"), "runtime.model"),
            output_format=_text(data.get("outputFormat", "stream-json"), "runtime.outputFormat"),
            main_timeout_seconds=_positive_int(
                data.get("mainTimeoutSeconds", 4200), "runtime.mainTimeoutSeconds"
            ),
            checkpoint_timeout_seconds=_positive_int(
                data.get("checkpointTimeoutSeconds", 300), "runtime.checkpointTimeoutSeconds"
            ),
            max_cycles=_positive_int(data.get("maxCycles", 1), "runtime.maxCycles", 1000),
            extra_args=_string_tuple(data.get("extraArgs", ()), "runtime.extraArgs"),
            inherit_env=inherit_env,
            env=env,
        )


@dataclass(frozen=True)
class ParallelismConfig:
    root_workers: int
    subagents_per_worker: int
    shard_strategy: str
    subagent_roles: Tuple[str, ...]
    serialize_validation: bool

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ParallelismConfig":
        data = _object(value, "parallelism")
        strategy = _identifier(data.get("shardStrategy", "balanced-units"), "parallelism.shardStrategy")
        if strategy not in {"balanced-units", "one-unit-per-worker"}:
            raise ConfigError("unsupported parallelism.shardStrategy")
        serialize = data.get("serializeValidation", True)
        if not isinstance(serialize, bool):
            raise ConfigError("parallelism.serializeValidation must be boolean")
        roles = _string_tuple(
            data.get("subagentRoles", DEFAULT_SUBAGENT_ROLES), "parallelism.subagentRoles"
        )
        subagents = _positive_int(
            data.get("subagentsPerWorker", min(3, len(roles) or 1)),
            "parallelism.subagentsPerWorker",
            16,
        )
        if subagents > len(roles):
            raise ConfigError("parallelism.subagentsPerWorker exceeds subagentRoles")
        return cls(
            root_workers=_positive_int(data.get("rootWorkers", 1), "parallelism.rootWorkers", 32),
            subagents_per_worker=subagents,
            shard_strategy=strategy,
            subagent_roles=roles,
            serialize_validation=serialize,
        )


@dataclass(frozen=True)
class WorkflowConfig:
    campaign_id: str
    runtime: RuntimeConfig
    parallelism: ParallelismConfig
    phases: Tuple[Phase, ...]
    terminal_states: Tuple[str, ...]
    candidate_limit_per_unit: int
    prompt_dir: Path

    @classmethod
    def load(cls, path: Path) -> "WorkflowConfig":
        path = path.resolve()
        data = _load_json(path)
        if data.get("schema") != "generic-audit-workflow-v1":
            raise ConfigError("workflow schema must be generic-audit-workflow-v1")
        raw_phases = data.get("phases")
        if raw_phases is None:
            raw_phases = [
                {"id": phase_id, "minutes": minutes} for phase_id, minutes in DEFAULT_PHASES
            ]
        if not isinstance(raw_phases, list) or not raw_phases:
            raise ConfigError("phases must be a non-empty array")
        phases = tuple(Phase.from_dict(item, index) for index, item in enumerate(raw_phases))
        if len({phase.id for phase in phases}) != len(phases):
            raise ConfigError("phase ids must be unique")
        prompt_dir_raw = _text(data.get("promptDir", "builtin:generic"), "promptDir")
        if prompt_dir_raw == "builtin:generic":
            prompt_dir = (Path(__file__).resolve().parents[3] / "prompts").resolve()
        else:
            prompt_dir = Path(prompt_dir_raw)
            if not prompt_dir.is_absolute():
                prompt_dir = (path.parent / prompt_dir).resolve()
        return cls(
            campaign_id=_identifier(data.get("campaignId"), "campaignId"),
            runtime=RuntimeConfig.from_dict(data.get("runtime", {})),
            parallelism=ParallelismConfig.from_dict(data.get("parallelism", {})),
            phases=phases,
            terminal_states=_string_tuple(
                data.get(
                    "terminalStates",
                    ("COMPLETE", "NO_QUALIFIED_CANDIDATE", "BLOCKED", "CANCELLED"),
                ),
                "terminalStates",
            ),
            candidate_limit_per_unit=_positive_int(
                data.get("candidateLimitPerUnit", 3), "candidateLimitPerUnit", 100
            ),
            prompt_dir=prompt_dir,
        )

    def validate_runtime_assets(self) -> None:
        for name in ("controller.md", "roles.md", "blind-verifier.md", "checkpoint.md"):
            if not (self.prompt_dir / name).is_file():
                raise ConfigError("missing prompt template: %s" % (self.prompt_dir / name))


@dataclass(frozen=True)
class AnalysisUnit:
    id: str
    path: str
    focus: Tuple[str, ...] = ()
    weight: int = 1
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, value: Mapping[str, Any], index: int) -> "AnalysisUnit":
        data = _object(value, "units[%d]" % index)
        return cls(
            id=_identifier(data.get("id"), "units[%d].id" % index),
            path=_safe_relative_path(data.get("path", "."), "units[%d].path" % index),
            focus=_string_tuple(data.get("focus", ()), "units[%d].focus" % index),
            weight=_positive_int(data.get("weight", 1), "units[%d].weight" % index, 1000000),
            metadata=_object(data.get("metadata", {}), "units[%d].metadata" % index),
        )


@dataclass(frozen=True)
class TargetProfile:
    id: str
    display_name: str
    source_kind: str
    source_root: Path
    revision: str
    units: Tuple[AnalysisUnit, ...]
    interfaces: Mapping[str, Mapping[str, Any]]
    threat_model: Mapping[str, Any]
    evidence_rules: Mapping[str, Any]
    profile_path: Path

    @classmethod
    def load(cls, path: Path) -> "TargetProfile":
        path = path.resolve()
        data = _load_json(path)
        if data.get("schema") != "audit-target-profile-v1":
            raise ConfigError("target schema must be audit-target-profile-v1")
        source = _object(data.get("source"), "source")
        kind = _identifier(source.get("adapter"), "source.adapter")
        if kind not in {"git-repository", "directory-tree", "decompiled-tree"}:
            raise ConfigError("unsupported source.adapter: " + kind)
        root = Path(_text(source.get("root"), "source.root"))
        if not root.is_absolute():
            root = (path.parent / root).resolve()
        revision = str(source.get("revision", "")).strip()
        if kind == "git-repository" and not revision:
            raise ConfigError("git-repository source requires an immutable revision")
        raw_units = data.get("units", ())
        if not isinstance(raw_units, Sequence) or isinstance(raw_units, (str, bytes)):
            raise ConfigError("units must be an array")
        units = tuple(AnalysisUnit.from_dict(item, index) for index, item in enumerate(raw_units))
        if len({unit.id for unit in units}) != len(units):
            raise ConfigError("unit ids must be unique")
        interfaces = _object(data.get("interfaces"), "interfaces")
        unknown = set(interfaces) - set(INTERFACE_NAMES)
        if unknown:
            raise ConfigError("unknown target interfaces: " + ", ".join(sorted(unknown)))
        normalized: Dict[str, Mapping[str, Any]] = {}
        for name in INTERFACE_NAMES:
            interface = _object(interfaces.get(name, {"adapter": "none"}), "interfaces." + name)
            adapter = _identifier(interface.get("adapter", "none"), "interfaces.%s.adapter" % name)
            interface["adapter"] = adapter
            normalized[name] = interface
        normalized["source"] = dict(normalized["source"], adapter=kind, root=str(root), revision=revision)
        return cls(
            id=_identifier(data.get("id"), "id"),
            display_name=_text(data.get("displayName"), "displayName"),
            source_kind=kind,
            source_root=root,
            revision=revision,
            units=units,
            interfaces=normalized,
            threat_model=_object(data.get("threatModel", {}), "threatModel"),
            evidence_rules=_object(data.get("evidenceRules", {}), "evidenceRules"),
            profile_path=path,
        )

