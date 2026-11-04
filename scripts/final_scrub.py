"""Final step: scan output files for AI provenance marks and strip metadata/invisible chars.

Wraps guillaumemeyer/watermarks-remover (deterministic Layer A + document metadata only).
Visible body text must stay identical; otherwise the file is left untouched and reported.
Statistical (Layer B) rewriting is never run because it would change approved text.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
import zipfile
from html import unescape
from pathlib import Path

from contracts import file_hash

REPO_URL = "https://github.com/guillaumemeyer/watermarks-remover"
PINNED_COMMIT = "5c18093"
DEFAULT_TOOL_DIR = Path.home() / ".cache" / "watermarks-remover"
TEXT_EXT = {".md", ".txt"}
DOCX_EXT = {".docx"}


def visible_text(path):
    """Body text with format/invisible characters removed and spaces normalized."""
    path = Path(path)
    if path.suffix.lower() in DOCX_EXT:
        xml = zipfile.ZipFile(path).read("word/document.xml").decode("utf-8")
        raw = unescape("".join(re.findall(r"<w:t(?: [^>]*)?>(.*?)</w:t>", xml, flags=re.S)))
    else:
        raw = path.read_text(encoding="utf-8")
    kept = "".join(ch for ch in raw if unicodedata.category(ch) != "Cf")
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", kept)).strip()


def _run(tool, script, *args):
    proc = subprocess.run(
        [sys.executable, "-I", str(tool / "service" / "scripts" / script), *map(str, args), "--json"],
        capture_output=True,
        text=True,
        timeout=600,
    )
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"error": (proc.stderr or proc.stdout)[-500:]}


def _dirty(report):
    return bool(
        report.get("findings")
        or report.get("layer_a_hits")
        or report.get("has_ai_metadata")
        or report.get("has_c2pa")
        or report.get("suspicious_total")
    )


def tool_dir(arg):
    tool = Path(arg or os.environ.get("WATERMARKS_REMOVER_DIR") or DEFAULT_TOOL_DIR)
    if not (tool / "service" / "scripts" / "clean_file.py").is_file():
        return None, None
    head = subprocess.run(
        ["git", "-C", str(tool), "rev-parse", "--short=7", "HEAD"], capture_output=True, text=True
    ).stdout.strip()
    return tool, head


def scrub(root, files, tool, backup_dir):
    results = []
    for path in files:
        entry = {"path": str(path.relative_to(root)) if path.is_relative_to(root) else str(path)}
        if path.suffix.lower() not in TEXT_EXT | DOCX_EXT:
            entry["action"] = "unsupported format, not modified"
            results.append(entry)
            continue
        before = _run(tool, "inspect_file.py", path)
        entry["findings"] = before.get("findings", []) + before.get("layer_a_hits", [])
        if "error" in before:
            entry["action"] = "inspect failed"
            entry["error"] = before["error"]
        elif not _dirty(before):
            entry["action"] = "clean, not modified"
        else:
            with tempfile.TemporaryDirectory() as tmp:
                out = Path(tmp) / path.name
                cleaned = _run(tool, "clean_file.py", path, "-o", out)
                if not out.is_file():
                    entry["action"] = "clean failed"
                    entry["error"] = cleaned.get("error", "no output")
                elif visible_text(out) != visible_text(path):
                    entry["action"] = "BLOCKED: visible text would change, original kept"
                else:
                    backup_dir.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(path, backup_dir / f"{path.name}.pre-scrub")
                    entry["sha256_before"] = file_hash(path)
                    shutil.copyfile(out, path)
                    entry["sha256_after"] = file_hash(path)
                    entry["removed"] = cleaned.get("actions", [])
                    after = _run(tool, "inspect_file.py", path)
                    entry["action"] = "cleaned" if not _dirty(after) else "cleaned, findings remain"
                    entry["remaining"] = after.get("findings", [])
        results.append(entry)
    return results


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("application_dir", type=Path)
    p.add_argument("--files", nargs="*", type=Path, help="default: output/*.docx|md|txt")
    p.add_argument("--tool-dir")
    args = p.parse_args()
    root = args.application_dir.resolve()
    tool, head = tool_dir(args.tool_dir)
    if tool is None:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": "watermarks-remover not found",
                    "install": f"git clone {REPO_URL} {DEFAULT_TOOL_DIR} && "
                    f"git -C {DEFAULT_TOOL_DIR} checkout {PINNED_COMMIT}",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 2
    files = [f.resolve() for f in args.files] if args.files else sorted(
        f for f in (root / "output").iterdir()
        if f.is_file() and f.suffix.lower() in TEXT_EXT | DOCX_EXT
    )
    results = scrub(root, files, tool, root / "workspace" / "backup")
    report = {
        "tool": f"{REPO_URL}@{head}",
        "pinned_commit": PINNED_COMMIT,
        "commit_matches_pin": head.startswith(PINNED_COMMIT),
        "scope": "Layer A invisible chars + document metadata; Layer B rewrite not run",
        "files": results,
    }
    manifest = root / "output" / "export-manifest.json"
    if manifest.is_file():
        data = json.loads(manifest.read_text(encoding="utf-8"))
        data["final_scrub"] = report
        manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    ok = all(not r["action"].startswith(("BLOCKED", "clean failed", "inspect failed")) for r in results)
    print(json.dumps({"ok": ok, **report}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
