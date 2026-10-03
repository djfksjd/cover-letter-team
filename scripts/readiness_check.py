"""Audit required-component evidence coverage; semantic sufficiency is a stated judgment."""

import argparse
import json
from pathlib import Path

from contracts import get_field, load_yaml, project_path
from validate_application import (
    _cards,
    _config,
    _envelope,
    _object,
    _questions,
    _text,
    _unique_rows,
)

STATUSES = {
    "SUFFICIENT",
    "UNKNOWN",
    "MISSING",
    "CONTRADICTORY",
    "WEAKLY_SUPPORTED",
    "NOT_APPLICABLE",
    "NO_ACTUAL_EXPERIENCE",
}


def assess(requirements, cards, plan, app_id):
    questions = _questions(requirements, app_id)
    _envelope(plan, app_id, "evidence-plan")
    coverage = _unique_rows(plan.get("coverage"), "coverage")
    expected = {f"{qid}/{c['id']}": c for qid, q in questions.items() for c in q["components"]}
    if set(coverage) - set(expected):
        raise ValueError("Coverage references an unknown question/component")
    gaps = []
    for key, component in expected.items():
        row = coverage.get(key)
        if row is None:
            if component["mandatory"]:
                gaps.append(
                    {
                        "id": key,
                        "type": "MISSING",
                        "blocking": True,
                        "decision_method": "deterministic",
                        "reason": "Required component has no evidence mapping",
                        "resolution_owner": "director",
                        "ask": "Map existing evidence first; ask the applicant only if missing.",
                    }
                )
            continue
        if row.get("status") not in STATUSES:
            raise ValueError(f"{key}: invalid evidence status")
        _text(row.get("rationale"), f"{key}.rationale")
        _text(row.get("resolution_owner"), f"{key}.resolution_owner")
        refs = row.get("references")
        if not isinstance(refs, list):
            raise ValueError("Coverage references must be a list")
        invalid = False
        for ref in refs:
            _object(ref, "coverage reference")
            card = cards.get(ref.get("card_id"))
            if not card:
                invalid = True
                continue
            gate = "verified" if ref["card_id"].startswith("RSH-") else "user_confirmed"
            if not card[gate]:
                invalid = True
            field = _text(ref.get("field"), "coverage field")
            if field.split(".")[0] in {
                "id",
                "application_id",
                "schema_version",
                "approval",
                "user_confirmed",
                "verified",
            }:
                raise ValueError("Gate/identity fields are not coverage evidence")
            value = get_field(card, field)
            if not value:
                invalid = True
        status = row["status"]
        if status == "SUFFICIENT" and (not refs or invalid):
            status = "WEAKLY_SUPPORTED"
        if component["mandatory"] and status == "NOT_APPLICABLE":
            status = "CONTRADICTORY"
        if status != "SUFFICIENT" and (component["mandatory"] or status != "NOT_APPLICABLE"):
            gaps.append(
                {
                    "id": key,
                    "type": status,
                    "blocking": component["mandatory"],
                    "decision_method": "deterministic" if invalid else "evidence_based_judgment",
                    "reason": row["rationale"],
                    "resolution_owner": row["resolution_owner"],
                    "ask": row.get("ask"),
                    "repeat_question": False if status == "NO_ACTUAL_EXPERIENCE" else None,
                }
            )
    blocking = any(g["blocking"] for g in gaps)
    return {
        "ok": not blocking,
        "state": "NEEDS_USER_INPUT" if blocking else "EVIDENCE_READY",
        "gaps": gaps,
        "limitations": "SUFFICIENT is a source-based judgment, not a measured hiring probability.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project")
    args = parser.parse_args()
    try:
        root = Path(args.project).resolve()
        app_id = _config(load_yaml(project_path(root, "workspace/application-config.yaml")))
        result = assess(
            load_yaml(project_path(root, "workspace/requirements.yaml")),
            _cards(root, app_id),
            load_yaml(project_path(root, "workspace/evidence-plan.yaml")),
            app_id,
        )
    except (ValueError, OSError, KeyError, IndexError, TypeError, RecursionError) as exc:
        result = {"ok": False, "state": "DRAFT_WITH_ISSUES", "errors": [str(exc)]}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
