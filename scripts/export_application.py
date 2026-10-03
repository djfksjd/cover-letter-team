"""Export only a current reviewed and user-confirmed v2 draft. Never submits it."""

import argparse
import json
import os
import tempfile
import shutil
from pathlib import Path

from contracts import file_hash, load_yaml, project_path, text_hash
from docx_convert import md_to_docx, verify_roundtrip
from validate_application import validate
from submission_render import submission_text


def export(root, draft, review, approval):
    result = validate(root, draft, review, approval)
    if not result["ok"]:
        return result
    root = Path(root).resolve()
    source = project_path(root, draft).read_text(encoding="utf-8")
    if text_hash(source) != result["draft_hash"]:
        return {"ok": False, "errors": ["Draft changed during export"]}
    config = load_yaml(project_path(root, "workspace/application-config.yaml"))
    requirements = load_yaml(project_path(root, "workspace/requirements.yaml"))
    clean = submission_text(source, config["document_type"], requirements)
    review_data = load_yaml(project_path(root, review))
    files = review_data.get("file_reviews", [])
    output = project_path(root, "output")
    output.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".export-", dir=output) as temp:
        temp = Path(temp)
        (temp / "application.md").write_text(clean, encoding="utf-8")
        if files:
            shutil.copyfile(project_path(root, files[0]["path"]), temp / "application.docx")
            if file_hash(temp / "application.docx") != files[0]["sha256"]:
                return {"ok": False, "errors": ["Reviewed preview changed during export"]}
        else:
            md_to_docx(clean, str(temp / "application.docx"))
        if not verify_roundtrip(clean, str(temp / "application.docx")):
            return {"ok": False, "errors": ["DOCX text roundtrip mismatch"]}
        # Revalidate all approval inputs before exposing any output.
        latest = validate(root, draft, review, approval)
        if not latest["ok"] or latest.get("input_hash") != result["input_hash"]:
            return {"ok": False, "errors": ["Inputs changed during export"]}
        manifest = {
            "application_id": result["application_id"],
            "input_hash": result["input_hash"],
            "draft_hash": result["draft_hash"],
            "exported_text_hash": text_hash(clean),
            "state": "EXPORTED",
            "docx_sha256": file_hash(temp / "application.docx"),
            "layout_status": "reviewed_preview" if files else "requires_visual_check",
            "submitted": False,
        }
        (temp / "export-manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        for name in ["application.md", "application.docx", "export-manifest.json"]:
            os.replace(temp / name, output / name)
    return {"ok": True, **manifest}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project")
    parser.add_argument("--draft", required=True)
    parser.add_argument("--review", required=True)
    parser.add_argument("--approval", required=True)
    args = parser.parse_args()
    try:
        result = export(args.project, args.draft, args.review, args.approval)
    except (ValueError, OSError) as exc:
        result = {"ok": False, "errors": [str(exc)]}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
