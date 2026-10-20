"""Run a bounded, real source-review session for the operation video.

Raw logs stay in tmp. Exported records replace machine-specific paths, and omit
model reasoning and credentials. No model result is invented by this script.
"""
import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import time
import tomllib
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SESSION = ROOT / "tmp/operation-demo"
SOURCE = ROOT / "tmp/demo-source-c-utils"
EXPORT = ROOT / "reports/operation-demo"


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def clean(value):
    text = str(value)
    # Both slash forms occur in CLI and JSON output.
    for source, replacement in [(str(ROOT), "<PROJECT>"), (str(Path.home()), "<USER>")]:
        for variant in (source.replace("\\", "\\\\"), source, source.replace("\\", "/")):
            text = text.replace(variant, replacement)
    return text


def run(name, args, env, timeout=120):
    start = time.perf_counter()
    started = datetime.now(timezone.utc).isoformat()
    result = subprocess.run(args, cwd=ROOT, env=env, capture_output=True, text=True,
                            encoding="utf-8", errors="replace", timeout=timeout)
    output = result.stdout + result.stderr
    (SESSION / (name + ".raw.log")).write_text(output, encoding="utf-8")
    record = {"name": name, "started_at": started, "duration_seconds": time.perf_counter()-start,
              "command": [clean(a) for a in args], "exit_code": result.returncode,
              "stdout": clean(result.stdout), "stderr": clean(result.stderr),
              "raw_output_sha256": hashlib.sha256(output.encode()).hexdigest()}
    write_json(EXPORT / (name + ".json"), record)
    print(name, "exit", result.returncode, flush=True)
    if result.returncode:
        raise RuntimeError(name + " failed: " + clean(output[-1600:]))
    return record


def prepare(env):
    if (SESSION/"run/plan.json").exists():
        raise SystemExit("Existing task preserved. Choose a fresh --session-dir for another run.")
    if not SOURCE.is_dir():
        raise SystemExit("Clone https://github.com/openharmony/commonlibrary_c_utils.git to tmp/demo-source-c-utils first")
    revision = subprocess.check_output(["git", "-C", str(SOURCE), "rev-parse", "HEAD"], text=True).strip()
    config = tomllib.loads((Path.home()/".codex/config.toml").read_text(encoding="utf-8"))
    model = config["model"]
    native = shutil.which("codex.exe")
    if not native:
        native = shutil.which("codex")
    if not native:
        raise SystemExit("Codex CLI is required")
    workflow = json.loads((ROOT/"config/workflow.audit.example.json").read_text(encoding="utf-8"))
    workflow.update(campaignId="parcel-operation-demo", promptDir=str(ROOT/"prompts"))
    workflow["runtime"] = {"adapter":"codex", "command":native, "model":model,
        "outputFormat":"jsonl", "mainTimeoutSeconds":480, "checkpointTimeoutSeconds":90,
        "maxCycles":1, "extraArgs":[], "inheritEnv":[], "env":{}}
    workflow["parallelism"].update(rootWorkers=1, subagentsPerWorker=1,
                                    subagentRoles=["dataflow-lifetime"])
    target = {"schema":"audit-target-profile-v1", "id":"c-utils-parcel-demo",
        "displayName":"OpenHarmony c_utils / Parcel capacity review",
        "source":{"adapter":"git-repository","root":str(SOURCE),"revision":revision},
        "units":[{"id":"parcel-write-buffer","path":"base/src/parcel.cpp",
                  "focus":["WriteBuffer","EnsureWritableCapacity","WriteDataBytes"],"weight":1}],
        "interfaces":{"source":{"adapter":"git-repository"},
                      "history":{"adapter":"none"}, "staticAnalysis":{"adapter":"none"},
                      "validation":{"adapter":"none"}, "novelty":{"adapter":"none"}},
        "threatModel":{"actors":["caller supplying buffer and length"],
                       "trustBoundaries":["Parcel public API"]},
        "evidenceRules":{"requireBlindVerification":True,"staticOnlyLabel":"STATIC_ONLY"}}
    write_json(SESSION/"workflow.json",workflow)
    write_json(SESSION/"target.json",target)
    relative = SESSION.relative_to(ROOT).as_posix()
    common = ["--workflow",relative+"/workflow.json","--target",relative+"/target.json"]
    base = [sys.executable,"-m","openharmony_audit","workflow"]
    run("01-environment",[sys.executable,"--version"],env)
    run("02-install",[sys.executable,"-m","pip","install","-e",".","--no-deps"],env)
    run("03-codex-version",[native,"--version"],env)
    run("04-validate",[*base,"validate",*common,"--strict-source"],env)
    run("05-plan",[*base,"plan",*common],env)
    run("06-prepare",[*base,"prepare",*common,"--run-root",relative+"/run"],env)
    run("07-status-before",[*base,"status","--run-root",relative+"/run"],env)
    worker=SESSION/"run/workers/worker-1"
    prompt=worker/"prompt.md"
    prompt.write_text(prompt.read_text(encoding="utf-8")+"""

## 本次小范围操作演示的执行约束

这次任务用于记录真实源码审计操作，重点是跑通范围确认、源码读取、保护条件核对和结果落盘。
使用一个控制器，顺序检查三个视角：入口参数、容量/写入数据流、已有保护条件。
不要启动子代理。只读目标源码，目标文件是 base/src/parcel.cpp；可参考 base/include/parcel.h。
只审查 WriteBuffer、EnsureWritableCapacity、WriteDataBytes 及必要的直接辅助函数。
不展开未知漏洞挖掘，不编译，不运行 PoC，不调用网络或 CodeQL，不修改目标文件。
独立盲验证和动态验证在本次任务范围以外，报告记录本次完成的源码检查即可。
请在约 12 次文件/命令操作内完成。使用工具实际读取源码，并保留准确行号。
在当前 worker 目录写以下文件，所有说明使用中文：
1. source-review.json：schema="parcel-source-review-v1"，snapshot=<本次commit>，
   scope=[实际检查的函数]，checks=[{function, location, observation, protection, follow_up}]，
   outcome="SOURCE_REVIEW_COMPLETE"，candidate_count=<实际候选数量，允许0>。
   checks 至少3项，记录事实和保护条件，不把猜测记成确认漏洞。
2. review-report.md：简短的源码检查记录，包括目标版本、函数范围、检查结果、源码位置和后续复核点。
   每个函数一小段，整体不超过600个汉字；清楚区分已观察事实与后续问题。
3. checkpoint.json：已完成函数、产物路径和后续可执行事项。
4. worker-state.json：state="COMPLETE"、terminal=true、scope="bounded-source-review"、
   completed_units、artifacts、candidate_count、last_complete_artifact。
完成后在最终回答中简短列出文件与检查范围。不得读用户认证文件或与任务无关的私人目录。
""",encoding="utf-8")
    text=(SOURCE/"base/src/parcel.cpp").read_text(encoding="utf-8")
    write_json(EXPORT/"session.json",{
        "schema":"operation-demo-session-v1", "source_url":"https://github.com/openharmony/commonlibrary_c_utils",
        "revision":revision,"model":model,"runtime":"codex", "source_file":"base/src/parcel.cpp",
        "source_file_lines":len(text.splitlines()),"source_file_sha256":hashlib.sha256((SOURCE/"base/src/parcel.cpp").read_bytes()).hexdigest(),
        "scope":"WriteBuffer / EnsureWritableCapacity / WriteDataBytes (bounded source review)",
        "python":platform.python_version(), "os":platform.system(),
        "workflow":json.loads(clean(json.dumps(workflow,ensure_ascii=False))),
        "target":json.loads(clean(json.dumps(target,ensure_ascii=False))),
        "display_note":"Machine-specific paths are replaced with <PROJECT> and <USER>."})
    lines=text.splitlines()
    write_json(EXPORT/"source-excerpt.json",{"attribution":"Copyright (c) 2021 Huawei Device Co., Ltd.; Apache-2.0",
        "source_url":"https://github.com/openharmony/commonlibrary_c_utils/blob/"+revision+"/base/src/parcel.cpp",
        "lines":[{"number":n,"text":lines[n-1]} for n in range(409,433)]})


def audit(env):
    relative=SESSION.relative_to(ROOT).as_posix()
    state_path=SESSION/"run/workers/worker-1/worker-state.json"
    if state_path.exists() and json.loads(state_path.read_text(encoding="utf-8")).get("terminal"):
        raise SystemExit("Completed task preserved. Prepare a fresh session before remeasuring.")
    meta=json.loads((EXPORT/"session.json").read_text(encoding="utf-8"))
    run("08-run",[sys.executable,"scripts/measure_command.py","--output",relative+"/measurement.json",
        "--scope","bounded-parcel-source-review","--snapshot",meta["revision"],"--",
        sys.executable,"-m","openharmony_audit","workflow","run","--run-root",relative+"/run"],env,660)
    run("09-status-after",[sys.executable,"-m","openharmony_audit","workflow","status",
                           "--run-root",relative+"/run"],env)
    worker=SESSION/"run/workers/worker-1"
    state=json.loads((worker/"worker-state.json").read_text(encoding="utf-8"))
    if not state.get("terminal") or state.get("state")!="COMPLETE":
        raise RuntimeError("Source review has not completed")
    for name in ["source-review.json","review-report.md","checkpoint.json","worker-state.json"]:
        data=(worker/name).read_text(encoding="utf-8")
        (EXPORT/name).write_text(clean(data),encoding="utf-8")
    shutil.copyfile(SESSION/"measurement.json",EXPORT/"measurement.json")
    events=[]
    for p in sorted(worker.glob("*.stream.jsonl")):
        for line in p.read_text(encoding="utf-8",errors="replace").splitlines():
            try:e=json.loads(line)
            except ValueError:continue
            typ=e.get("type")
            if typ in ["thread.started","turn.started","turn.completed","turn.failed"]:
                events.append({"type":typ,**({"usage":e["usage"]} if "usage" in e else {})})
            item=e.get("item",{})
            if typ=="item.completed" and item.get("type")=="command_execution":
                events.append({"type":"command.completed","command":clean(item.get("command","")),
                               "exit_code":item.get("exit_code")})
            if typ=="item.completed" and item.get("type")=="file_change":
                events.append({"type":"files.changed","changes":json.loads(clean(json.dumps(item.get("changes",[]))))})
    write_json(EXPORT/"events.json",events)
    print("Completed source review; exported factual records to reports/operation-demo",flush=True)


def main():
    global SESSION, EXPORT
    parser=argparse.ArgumentParser()
    parser.add_argument("stage",choices=["prepare","audit","all"])
    parser.add_argument("--session-dir",type=Path,default=SESSION)
    parser.add_argument("--export-dir",type=Path,default=EXPORT)
    args=parser.parse_args()
    SESSION=args.session_dir.resolve();EXPORT=args.export_dir.resolve()
    if not SESSION.is_relative_to(ROOT) or not EXPORT.is_relative_to(ROOT):
        parser.error("session and export directories must be within this project")
    SESSION.mkdir(parents=True,exist_ok=True);EXPORT.mkdir(parents=True,exist_ok=True)
    env=os.environ.copy()
    env.update(PYTHONUTF8="1",PYTHONIOENCODING="utf-8",
               PYTHONPATH=os.pathsep.join([str(ROOT/"src"),str(ROOT/"tmp/media-deps")]))
    if args.stage in ["prepare","all"]:prepare(env)
    if args.stage in ["audit","all"]:audit(env)


if __name__=="__main__":main()
