"""Claude Code runtime adapter with parallel root workers and checkpoint cycles."""

from __future__ import annotations

import json
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

from .generic_contracts import ConfigError


def _load(path: Path) -> Dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigError("cannot read runtime file %s: %s" % (path, exc)) from exc
    if not isinstance(value, dict):
        raise ConfigError("runtime file must contain a JSON object")
    return value


def claude_command(runtime: Mapping[str, Any]) -> List[str]:
    command = runtime.get("command")
    model = runtime.get("model")
    output_format = runtime.get("outputFormat", "stream-json")
    extra = runtime.get("extraArgs", [])
    if not isinstance(command, str) or not command:
        raise ConfigError("runtime command is missing")
    if not isinstance(model, str) or not model:
        raise ConfigError("runtime model is missing")
    if not isinstance(extra, list) or any(not isinstance(item, str) for item in extra):
        raise ConfigError("runtime extraArgs must be an array of strings")
    return [command, "-p", "--model", model, "--verbose", "--output-format", output_format] + extra


def _state_is_terminal(worker_root: Path, terminal_states: Sequence[str]) -> bool:
    state_path = worker_root / "worker-state.json"
    if not state_path.is_file():
        return False
    state = _load(state_path)
    return state.get("terminal") is True and state.get("state") in terminal_states


def _runtime_environment(runtime: Mapping[str, Any], worker_root: Path) -> Dict[str, str]:
    inherited = runtime.get("inheritEnv", [])
    if not isinstance(inherited, list) or any(not isinstance(item, str) for item in inherited):
        raise ConfigError("runtime.inheritEnv must be an array of variable names")
    common = ("PATH", "HOME", "TMPDIR", "SHELL", "LANG", "LC_ALL", "TERM")
    environment = {
        key: os.environ[key] for key in tuple(common) + tuple(inherited) if key in os.environ
    }
    environment["HOME"] = str(worker_root / "home")
    fixed = runtime.get("env", {})
    if not isinstance(fixed, dict):
        raise ConfigError("runtime.env must be an object")
    for key, value in fixed.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise ConfigError("runtime.env values must be strings")
        environment[key] = value
    model = str(runtime["model"])
    environment.update(
        {
            "ANTHROPIC_MODEL": model,
            "ANTHROPIC_DEFAULT_OPUS_MODEL": model,
            "ANTHROPIC_DEFAULT_SONNET_MODEL": model,
            "ANTHROPIC_DEFAULT_HAIKU_MODEL": model,
            "CLAUDE_CODE_SUBAGENT_MODEL": model,
        }
    )
    return environment


def _run_session(
    command: Sequence[str],
    prompt_path: Path,
    log_path: Path,
    cwd: Path,
    environment: Mapping[str, str],
    timeout_seconds: int,
) -> int:
    with prompt_path.open("rb") as prompt, log_path.open("ab") as log:
        try:
            completed = subprocess.run(
                list(command),
                stdin=prompt,
                stdout=log,
                stderr=subprocess.STDOUT,
                cwd=str(cwd),
                env=dict(environment),
                timeout=timeout_seconds,
                check=False,
            )
            return completed.returncode
        except subprocess.TimeoutExpired:
            return 124


def run_worker(plan: Mapping[str, Any], run_root: Path, worker_id: str) -> Dict[str, Any]:
    runtime = plan["runtime"]
    terminal_states = plan["terminalStates"]
    worker_root = run_root / "workers" / worker_id
    if not worker_root.is_dir():
        raise ConfigError("unknown worker: " + worker_id)
    command = claude_command(runtime)
    environment = _runtime_environment(runtime, worker_root)
    max_cycles = int(runtime["maxCycles"])
    events: List[Dict[str, Any]] = []
    for cycle in range(1, max_cycles + 1):
        if _state_is_terminal(worker_root, terminal_states):
            break
        main_status = _run_session(
            command,
            worker_root / "prompt.md",
            worker_root / ("controller-%03d.stream.jsonl" % cycle),
            worker_root,
            environment,
            int(runtime["mainTimeoutSeconds"]),
        )
        event: Dict[str, Any] = {"cycle": cycle, "controllerExit": main_status}
        if not _state_is_terminal(worker_root, terminal_states):
            checkpoint_status = _run_session(
                command,
                worker_root / "checkpoint-prompt.md",
                worker_root / ("checkpoint-%03d.stream.jsonl" % cycle),
                worker_root,
                environment,
                int(runtime["checkpointTimeoutSeconds"]),
            )
            event["checkpointExit"] = checkpoint_status
        events.append(event)
    return {
        "worker": worker_id,
        "terminal": _state_is_terminal(worker_root, terminal_states),
        "events": events,
    }


def run_parallel(
    plan: Mapping[str, Any],
    run_root: Path,
    selected_workers: Optional[Iterable[str]] = None,
) -> Dict[str, Any]:
    available = [worker["id"] for worker in plan["workers"]]
    selected = list(selected_workers or available)
    if not selected:
        raise ConfigError("at least one worker must be selected")
    unknown = set(selected) - set(available)
    if unknown:
        raise ConfigError("unknown workers: " + ", ".join(sorted(unknown)))
    results = []
    with ThreadPoolExecutor(max_workers=len(selected)) as pool:
        futures = {
            pool.submit(run_worker, plan, run_root, worker): worker for worker in selected
        }
        for future in as_completed(futures):
            results.append(future.result())
    results.sort(key=lambda item: item["worker"])
    return {
        "schema": "generic-audit-run-result-v1",
        "campaignId": plan["campaignId"],
        "workers": results,
        "terminal": all(item["terminal"] for item in results),
    }

