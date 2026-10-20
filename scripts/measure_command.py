"""Measure a command's wall time and sampled process-tree RSS (requires psutil)."""
import argparse
import json
import platform
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import psutil


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--scope", required=True, help="e.g. planner-only, source-audit, codeql-query")
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--interval", type=float, default=0.02)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command or args.interval <= 0:
        parser.error("provide a command and a positive sampling interval")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    peak = samples = 0
    started = datetime.now(timezone.utc).isoformat()
    start = time.perf_counter()
    with args.output.with_suffix(".stdout.log").open("wb") as log:
        child = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
        parent = psutil.Process(child.pid)
        while True:
            try:
                processes = [parent, *parent.children(recursive=True)]
            except psutil.Error:
                processes = []
            rss = 0
            for process in processes:
                try:
                    rss += process.memory_info().rss
                except psutil.Error:
                    pass
            peak = max(peak, rss)
            samples += 1
            if child.poll() is not None:
                break
            time.sleep(args.interval)
        returncode = child.wait()
    record = {
        "schema": "audit-performance-measurement-v1", "scope": args.scope,
        "snapshot": args.snapshot, "started_at": started,
        "wall_seconds": time.perf_counter() - start,
        "sampled_peak_process_tree_rss_bytes": peak, "sampling_interval_seconds": args.interval,
        "samples": samples, "returncode": returncode,
        "environment": {"os": platform.platform(), "machine": platform.machine(),
                        "processor": platform.processor(), "logical_cpus": psutil.cpu_count(),
                        "physical_memory_bytes": psutil.virtual_memory().total,
                        "monitor_python": platform.python_version()},
        "measurement_notes": "RSS sampled over parent and live descendants; shared pages may be counted twice. Short peaks or short-lived children may be missed. Monitor process excluded. No remote model memory is measured."
    }
    args.output.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, ensure_ascii=False))
    return returncode


if __name__ == "__main__":
    raise SystemExit(main())
