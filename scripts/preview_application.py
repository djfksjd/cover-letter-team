"""Create an unapproved preview for layout review; never writes output/ or consent."""

import argparse
import json
from pathlib import Path

from contracts import file_hash, load_yaml, project_path
from docx_convert import md_to_docx, verify_roundtrip
from submission_render import submission_text
from validate_application import validate


def preview(root, draft):
    result = validate(root, draft)
    if not result["ok"]:
        return result
    root = Path(root).resolve()
    source = project_path(root, draft).read_text(encoding="utf-8")
    config = load_yaml(project_path(root, "workspace/application-config.yaml"))
    requirements = load_yaml(project_path(root, "workspace/requirements.yaml"))
    clean = submission_text(source, config["document_type"], requirements)
    folder = project_path(root, "workspace/preview")
    folder.mkdir(exist_ok=True)
    (folder / "application.md").write_text(clean, encoding="utf-8")
    md_to_docx(clean, str(folder / "application.docx"))
    if not verify_roundtrip(clean, str(folder / "application.docx")):
        return {"ok": False, "errors": ["Preview text roundtrip mismatch"]}
    latest = validate(root, draft)
    if not latest["ok"] or latest.get("input_hash") != result["input_hash"]:
        return {"ok": False, "errors": ["Inputs changed during preview"]}
    manifest = {
        "state": "UNAPPROVED_PREVIEW",
        "submission_ready": False,
        "input_hash": result["input_hash"],
        "draft_hash": result["draft_hash"],
        "docx_sha256": file_hash(folder / "application.docx"),
        "layout_status": "not_reviewed",
    }
    (folder / "preview-manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return {"ok": True, **manifest}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project")
    parser.add_argument("--draft", required=True)
    args = parser.parse_args()
    try:
        result = preview(args.project, args.draft)
    except (ValueError, OSError) as exc:
        result = {"ok": False, "errors": [str(exc)]}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
