"""Package a committed source snapshot, with per-file SHA-256 provenance.

No untracked files, Git metadata, node_modules, credentials or run directories
are included. The source archive intentionally excludes delivery binaries.
"""
import hashlib
import io
import json
import subprocess
import zipfile
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=root)

    commit = git("rev-parse", "HEAD").decode().strip()
    allowed = {"src", "config", "prompts", "schemas", "docs", "reports", "frontend", "tests", "scripts"}
    root_files = {"README.md", "NOTICE.md", "pyproject.toml", ".gitignore", ".gitattributes"}
    paths = []
    for raw in git("ls-tree", "-r", "--name-only", "-z", "HEAD").split(b"\0"):
        if not raw:
            continue
        path = raw.decode("utf-8")
        parts = Path(path).parts
        if (parts[0] in allowed or path in root_files) and not any(
            p in {"node_modules", "__pycache__", ".env", "run-data", ".venv", "knowledge"} for p in parts
        ):
            paths.append(path)
    if not paths:
        raise RuntimeError("No committed sources to package")
    data = git("archive", "--format=zip", "HEAD", "--", *paths)
    dest = root / "deliverables/01-source.zip"
    dest.parent.mkdir(exist_ok=True)
    manifest = {"schema": "source-delivery-manifest-v1", "sourceCommit": commit,
                "repository": "https://github.com/Binnnn-Lab/OpenHarmony-Audit-Agent",
                "upstream": {"audit-workflow-prompts": "7bd9cd9cbea555980b347bfd71bd5e4e75087b9b",
                             "CodeQL-AI": "51dbf412f440f723746087588665646c0edadddd"}, "files": []}
    with zipfile.ZipFile(io.BytesIO(data)) as source, zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as target:
        for name in source.namelist():
            if name.endswith("/"):
                continue
            content = source.read(name)
            target.writestr(name, content)
            manifest["files"].append({"path": name, "bytes": len(content), "sha256": hashlib.sha256(content).hexdigest()})
        target.writestr("SOURCE-MANIFEST.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(f"Packaged {len(manifest['files'])} files from {commit} into {dest.name}")


if __name__ == "__main__":
    main()
