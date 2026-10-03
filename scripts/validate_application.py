"""Validate v2 application contracts, evidence coverage and fresh review/approval.

Does not infer semantic truth. Reviewer attestations are explicit, hash-bound inputs.
"""

import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlparse

from charcount import count_units, split_questions
from claim_check import CLAIM, check_claims
from submission_render import render_body
from contracts import (
    card_hash,
    digest,
    file_hash,
    get_field,
    load_yaml,
    project_path,
    read_cards,
    text_hash,
)

CARD_FILES = [
    ("experience-cards.yaml", "EXP", "user_confirmed"),
    ("research-evidence.yaml", "RSH", "verified"),
    ("fit-cards.yaml", "FIT", "user_confirmed"),
]
QUALITY_CHECKS = {
    "factual_consistency",
    "role_and_causality",
    "precision_and_privacy",
    "relevance_and_specificity",
    "language_and_voice",
    "submission_policy",
}
UNITS = {
    "characters_with_spaces",
    "characters_without_spaces",
    "words",
    "utf8_bytes",
    "utf16_units",
}
DOCUMENTS = {
    "question_answers",
    "cover_letter",
    "supporting_statement",
    "personal_statement",
    "selection_criteria",
}


def _object(value, name):
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")
    return value


def _text(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a nonempty string")
    return value


def _envelope(value, app_id, name):
    _object(value, name)
    if type(value.get("schema_version")) is not int or value["schema_version"] != 2:
        raise ValueError(f"{name}: schema_version must be 2; migrate legacy files explicitly")
    if value.get("application_id") != app_id:
        raise ValueError(f"{name}: application identity mismatch")


def _unique_rows(rows, name):
    if not isinstance(rows, list):
        raise ValueError(f"{name} must be a list")
    result = {}
    for row in rows:
        _object(row, name)
        key = _text(row.get("id"), f"{name}.id")
        if key in result:
            raise ValueError(f"{name}: duplicate ID {key}")
        result[key] = row
    return result


def _config(config):
    _object(config, "config")
    app_id = _text(config.get("application_id"), "application_id")
    _envelope(config, app_id, "config")
    if config.get("mode") != "targeted_application":
        raise ValueError("Only targeted_application can be marked submission-ready")
    for key in ["hiring_country", "output_language", "career_level"]:
        _text(config.get(key), key)
    if config.get("document_type") not in DOCUMENTS:
        raise ValueError("Unsupported document_type")
    job = _object(config.get("job_identity"), "job_identity")
    for key in ["legal_entity", "title", "source_status"]:
        _text(job.get(key), f"job_identity.{key}")
    if job["source_status"] not in {"official_current", "user_provided"}:
        raise ValueError("Current target requirements must be official_current or user_provided")
    if config.get("ai_policy") not in {"allowed", "restricted", "prohibited", "unknown"}:
        raise ValueError("ai_policy must be explicit")
    if config["ai_policy"] == "prohibited":
        raise ValueError(
            "Employer prohibits AI-authored application; do not generate/export a submission"
        )
    if (
        "blind_hiring" not in config
        or config["blind_hiring"] is not None
        and type(config["blind_hiring"]) is not bool
    ):
        raise ValueError("blind_hiring must be boolean or null")
    if config["output_language"].startswith("ko") and config.get("ending_style") not in {
        "합쇼체",
        "평서체",
    }:
        raise ValueError("Korean ending_style must be configured")
    return app_id


def _questions(requirements, app_id):
    _envelope(requirements, app_id, "requirements")
    submission = requirements.get("submission", {})
    _object(submission, "submission")
    if (
        "file_review_required" in submission
        and type(submission["file_review_required"]) is not bool
    ):
        raise ValueError("file_review_required must be boolean")
    questions = _unique_rows(requirements.get("questions"), "questions")
    if not questions:
        raise ValueError("No application questions/body requirements")
    for key, question in questions.items():
        if not re.fullmatch(r"Q-\d{2,}", key):
            raise ValueError("Canonical question ID must be Q-NN")
        _text(question.get("prompt"), f"{key}.prompt")
        components = _unique_rows(question.get("components"), f"{key}.components")
        if not components:
            raise ValueError(f"{key}: at least one required content component is needed")
        for component in components.values():
            _text(component.get("text"), "component.text")
            if type(component.get("mandatory")) is not bool:
                raise ValueError("component.mandatory must be boolean")
            if component.get("source_status") not in {"explicit", "user_provided", "inferred"}:
                raise ValueError("component.source_status missing")
            if component["mandatory"] and component["source_status"] == "inferred":
                raise ValueError(
                    "Inferred rationale cannot silently become an employer requirement"
                )
        limit = _object(question.get("length"), f"{key}.length")
        if limit.get("unit") not in UNITS or limit.get("newline_policy") not in {
            "include",
            "exclude",
        }:
            raise ValueError(f"{key}: unsupported length/count policy")
        if limit.get("count_status") not in {"portal_verified", "approximate"}:
            raise ValueError(f"{key}: count_status required")
        for bound in ["minimum", "maximum"]:
            value = limit.get(bound)
            if value is not None and (type(value) is not int or value < 0):
                raise ValueError(f"{key}: {bound} must be a nonnegative integer or null")
        if (
            limit.get("minimum") is not None
            and limit.get("maximum") is not None
            and limit["minimum"] > limit["maximum"]
        ):
            raise ValueError(f"{key}: invalid length interval")
    return questions


def _cards(root, app_id):
    result = {}
    for filename, prefix, gate in CARD_FILES:
        data = read_cards(
            project_path(root, f"workspace/{filename}").read_text(encoding="utf-8"), prefix, gate
        )
        for key, card in data.items():
            _envelope(card, app_id, key)
            if card[gate]:
                approval = _object(card.get("approval"), f"{key}.approval")
                if approval.get("content_hash") != card_hash(card):
                    raise ValueError(f"{key}: stale card approval/verification")
                _text(approval.get("confirmed_at"), f"{key}.confirmed_at")
                expected_actor = "researcher" if prefix == "RSH" else "user"
                if approval.get("actor") != expected_actor:
                    raise ValueError(f"{key}: approval actor must be {expected_actor}")
            if prefix == "RSH" and card[gate]:
                for field in [
                    "claim",
                    "quote",
                    "url",
                    "retrieved_at",
                    "legal_entity",
                    "source_type",
                ]:
                    _text(card.get(field), f"{key}.{field}")
                if urlparse(card["url"]).scheme not in {"http", "https"}:
                    raise ValueError(f"{key}: evidence URL must be http(s)")
            result[key] = card
    return result


def claim_spans(draft):
    """Canonical spans preserve all text; Reviewer checks sentence-level granularity."""
    sections = split_questions(draft)
    if sections:
        first = re.search(r"^## Q-\d{2,}\b.*$", draft, re.MULTILINE)
        if not first or draft[: first.start()].strip():
            raise ValueError(
                "Draft preamble is not submission content; use only canonical Q headings"
            )
    rows = []
    for title, body in sections:
        key = title.split()[0]
        if not re.fullmatch(r"Q-\d{2,}", key):
            raise ValueError("v2 drafts require canonical ## Q-NN headings")
        if re.search(r"^#+\s", body, re.MULTILINE):
            raise ValueError(
                f"{key}: nested Markdown headings unsupported; subheadings are plain annotated text"
            )
        cursor = 0
        for marker in CLAIM.finditer(body):
            span = body[cursor : marker.start()].strip()
            if not span:
                raise ValueError(f"{key}: claim marker has no text")
            if "<!--" in span or "-->" in span:
                raise ValueError(f"{key}: unsupported/malformed comment")
            rows.append(
                {
                    "question_id": key,
                    "text": span,
                    "label": marker[1],
                    "card_ids": [] if marker[2] == "NONE" else marker[2].split(","),
                }
            )
            cursor = marker.end()
        if body[cursor:].strip():
            raise ValueError(f"{key}: unannotated trailing text")
    if not rows:
        raise ValueError("Draft has no annotated content")
    return sections, rows


def _claim_map(claim_map, spans, cards, app_id):
    _envelope(claim_map, app_id, "claim-map")
    records = _unique_rows(claim_map.get("claims"), "claims")
    if len(records) != len(spans):
        raise ValueError("Claim-map must cover every draft annotation exactly once")
    for row, span in zip(records.values(), spans):
        if not re.fullmatch(r"CLM-\d{3,}", row["id"]):
            raise ValueError("Claim ID must be CLM-NNN")
        for key in ["question_id", "text", "label"]:
            if row.get(key) != span[key]:
                raise ValueError(f"{row['id']}: claim-map text/order/label mismatch")
        refs = row.get("references")
        if not isinstance(refs, list):
            raise ValueError("references must be a list")
        if {ref.get("card_id") for ref in refs if isinstance(ref, dict)} != set(span["card_ids"]):
            raise ValueError(f"{row['id']}: references do not match annotation IDs")
        values = []
        for ref in refs:
            _object(ref, "reference")
            card = cards[ref["card_id"]]
            field = _text(ref.get("field"), "reference.field")
            if field.split(".")[0] in {
                "id",
                "application_id",
                "schema_version",
                "approval",
                "user_confirmed",
                "verified",
            }:
                raise ValueError("Gate/identity fields are not evidence of a claim")
            value = get_field(card, field)
            if (
                not isinstance(value, (str, int, float))
                or isinstance(value, bool)
                or not str(value).strip()
            ):
                raise ValueError("Reference must identify a nonempty scalar evidence field")
            if ref.get("value") != value or ref.get("card_hash") != card_hash(card):
                raise ValueError(f"{row['id']}: stale/fabricated evidence field")
            values.append(str(value))
        # This catches new Arabic numbers, not causality, unit changes or semantic lies.
        if span["label"] != "NONFACTUAL":
            numbers = set(re.findall(r"\d+(?:\.\d+)?", span["text"]))
            evidence_numbers = set(re.findall(r"\d+(?:\.\d+)?", " ".join(values)))
            if numbers - evidence_numbers:
                raise ValueError(
                    f"{row['id']}: numeric token absent from referenced evidence; add verified calculation evidence or remove it"
                )
    return records


def _review(review, app_id, input_hash, claims, questions):
    _envelope(review, app_id, "review")
    if review.get("input_hash") != input_hash:
        raise ValueError("Review is stale: inputs changed")
    if review.get("verdict") != "PASS" or review.get("unresolved_high") != []:
        raise ValueError("Review has unresolved blocking issues")
    _text(review.get("reviewer"), "review.reviewer")
    _text(review.get("reviewed_at"), "review.reviewed_at")
    reviewed = _unique_rows(review.get("claim_reviews"), "claim_reviews")
    if set(reviewed) != set(claims):
        raise ValueError("Semantic review must cover every claim, including NONFACTUAL")
    for key, record in reviewed.items():
        if record.get("verdict") != "PASS" or record.get("claim_hash") != digest(claims[key]):
            raise ValueError(f"{key}: semantic review failed/stale")
        _text(record.get("rationale"), f"{key}.rationale")
    component_reviews = _unique_rows(review.get("component_reviews"), "component_reviews")
    expected = {
        f"{qid}/{component['id']}": qid
        for qid, q in questions.items()
        for component in q["components"]
        if component["mandatory"]
    }
    if set(component_reviews) != set(expected):
        raise ValueError("Review must cover exactly all mandatory components")
    for key, row in component_reviews.items():
        ids = row.get("claim_ids")
        if row.get("verdict") != "PASS" or not isinstance(ids, list) or not ids:
            raise ValueError(f"{key}: required component not supported")
        if any(
            i not in claims
            or claims[i]["question_id"] != expected[key]
            or claims[i]["label"] == "NONFACTUAL"
            for i in ids
        ):
            raise ValueError(f"{key}: component evidence outside question/nonfactual")
        _text(row.get("rationale"), f"{key}.rationale")
    checks = _object(review.get("quality_checks"), "quality_checks")
    if set(checks) != QUALITY_CHECKS:
        raise ValueError("Review must address all quality dimensions")
    for key, check in checks.items():
        _object(check, key)
        if check.get("verdict") != "PASS":
            raise ValueError(f"Quality check failed: {key}")
        _text(check.get("rationale"), f"{key}.rationale")


def validate(root, draft="workspace/draft-v1.md", review=None, approval=None):
    """Return metadata only; diagnostics avoid copying private evidence text."""
    try:
        root = Path(root).resolve()
        config = load_yaml(project_path(root, "workspace/application-config.yaml"))
        app_id = _config(config)
        requirements = load_yaml(project_path(root, "workspace/requirements.yaml"))
        questions = _questions(requirements, app_id)
        if config["document_type"] != "question_answers" and len(questions) != 1:
            raise ValueError("Continuous document must have exactly one question section")
        cards = _cards(root, app_id)
        text = project_path(root, draft).read_text(encoding="utf-8")
        gates = {
            key: card["verified" if key.startswith("RSH-") else "user_confirmed"]
            for key, card in cards.items()
        }
        errs = check_claims(text, gates)
        if errs:
            raise ValueError("; ".join(errs))
        if re.search(r"\[(?:MATERIAL_GAP|COMPANY_FIT_GAP|TODO)|\{\{.*?\}\}", text):
            raise ValueError("Unresolved placeholder in draft")
        sections, spans = claim_spans(text)
        section_ids = [title.split()[0] for title, _ in sections]
        if section_ids != list(questions):
            raise ValueError("Question IDs/order mismatch: missing, duplicate or extra sections")
        counts = {}
        for title, body in sections:
            qid = title.split()[0]
            limit = questions[qid]["length"]
            counts[qid] = count_units(render_body(body), limit["unit"], limit["newline_policy"])
            if limit.get("maximum") is not None and counts[qid] > limit["maximum"]:
                raise ValueError(f"{qid}: official maximum exceeded")
            if limit.get("minimum") is not None and counts[qid] < limit["minimum"]:
                raise ValueError(f"{qid}: official minimum not met")
        from readiness_check import assess

        plan = load_yaml(project_path(root, "workspace/evidence-plan.yaml"))
        readiness = assess(requirements, cards, plan, app_id)
        if not readiness["ok"]:
            raise ValueError(
                "Required evidence gaps remain: "
                + ", ".join(g["id"] for g in readiness["gaps"] if g["blocking"])
            )
        claim_map = load_yaml(project_path(root, "workspace/claim-map.yaml"))
        claims = _claim_map(claim_map, spans, cards, app_id)
        input_hash = digest(
            {
                "validator_revision": "2.1-rendered-submission",
                "config": config,
                "requirements": requirements,
                "cards": cards,
                "claim_map": claim_map,
                "evidence_plan": plan,
                "draft": text,
            }
        )
        state = "DRAFT_VALIDATED"
        if approval and not review:
            raise ValueError("Export approval requires a review")
        review_data = None
        if review:
            review_data = load_yaml(project_path(root, review))
            _review(review_data, app_id, input_hash, claims, questions)
            required = requirements.get("submission", {}).get("file_review_required", False)
            files = review_data.get("file_reviews", [])
            if not isinstance(files, list) or (required and not files):
                raise ValueError("Required file layout review missing")
            if len(files) > 1:
                raise ValueError("Only the generated DOCX preview is supported for file review")
            for row in files:
                _object(row, "file_review")
                if row.get("path") != "workspace/preview/application.docx":
                    raise ValueError("Review only the current application preview file")
                path = project_path(root, row["path"])
                if row.get("verdict") != "PASS" or row.get("sha256") != file_hash(path):
                    raise ValueError("File review failed/stale")
                _text(row.get("rationale"), "file_review.rationale")
                preview_meta = load_yaml(
                    project_path(root, "workspace/preview/preview-manifest.json")
                )
                if (
                    preview_meta.get("input_hash") != input_hash
                    or preview_meta.get("docx_sha256") != row["sha256"]
                ):
                    raise ValueError("Preview is stale")
            state = "READY_FOR_USER_REVIEW"
        if approval:
            approved = load_yaml(project_path(root, approval))
            _envelope(approved, app_id, "final approval")
            if approved.get("user_confirmed") is not True or approved.get("actor") != "user":
                raise ValueError("Final approval requires explicit user confirmation")
            if approved.get("input_hash") != input_hash or approved.get("review_hash") != digest(
                review_data
            ):
                raise ValueError("Final approval is stale")
            if approved.get("draft_hash") != text_hash(text):
                raise ValueError("Approved draft differs from export draft")
            _text(approved.get("confirmed_at"), "final approval.confirmed_at")
            state = "APPROVED_FOR_EXPORT"
        return {
            "ok": True,
            "state": state,
            "application_id": app_id,
            "input_hash": input_hash,
            "draft_hash": text_hash(text),
            "counts": counts,
            "claim_hashes": {key: digest(row) for key, row in claims.items()},
            "review_hash": digest(review_data) if review_data else None,
            "limitations": [
                "Semantic truth relies on source-based Reviewer and applicant confirmation.",
                "Word/byte counts approximate the portal unless verified; file layout needs visual review.",
            ],
        }
    except (ValueError, OSError, KeyError, IndexError, TypeError, RecursionError) as exc:
        return {"ok": False, "state": "DRAFT_WITH_ISSUES", "errors": [str(exc)]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project")
    parser.add_argument("--draft", default="workspace/draft-v1.md")
    parser.add_argument("--review")
    parser.add_argument("--approval")
    args = parser.parse_args()
    result = validate(args.project, args.draft, args.review, args.approval)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
