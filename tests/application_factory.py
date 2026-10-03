"""Synthetic application fixtures. Approvals below are test data, never applicant consent."""

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from contracts import card_hash, digest, text_hash
from validate_application import QUALITY_CHECKS, validate


def put(root, name, value):
    path = root / "workspace" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, allow_unicode=True, sort_keys=False), encoding="utf-8")


def get(root, name):
    return yaml.safe_load((root / "workspace" / name).read_text(encoding="utf-8"))


def make_application(root, language="ko", document="question_answers", maximum=800, minimum=None):
    app_id = "APP-synthetic-001"
    meta = {"schema_version": 2, "application_id": app_id}
    config = {
        **meta,
        "mode": "targeted_application",
        "hiring_country": "KR" if language == "ko" else "GB",
        "output_language": language,
        "career_level": "entry",
        "document_type": document,
        "ending_style": "합쇼체" if language == "ko" else "not_applicable",
        "blind_hiring": False,
        "ai_policy": "allowed",
        "job_identity": {
            "legal_entity": "Synthetic Employer",
            "title": "Operations Analyst",
            "source_status": "user_provided",
        },
    }
    requirements = {
        **meta,
        "questions": [
            {
                "id": "Q-01",
                "prompt": "Describe your contribution to process improvement.",
                "components": [
                    {
                        "id": "C-01",
                        "text": "Personal action",
                        "mandatory": True,
                        "source_status": "user_provided",
                    },
                    {
                        "id": "C-02",
                        "text": "Actual outcome",
                        "mandatory": True,
                        "source_status": "user_provided",
                    },
                ],
                "length": {
                    "unit": "characters_with_spaces" if language == "ko" else "words",
                    "minimum": minimum,
                    "maximum": maximum,
                    "newline_policy": "exclude",
                    "count_status": "approximate",
                },
            }
        ],
    }
    action = "질문지를 작성했습니다." if language == "ko" else "I created a checklist for the team."
    outcome = (
        "팀이 인수인계에서 질문지를 사용했습니다."
        if language == "ko"
        else "The team used the checklist during handover."
    )
    card = {
        **meta,
        "id": "EXP-01",
        "event_id": "EVT-01",
        "personal_actions": [action],
        "team_result": [outcome],
        "precision": {},
        "user_confirmed": True,
    }
    card["approval"] = {
        "content_hash": card_hash(card),
        "actor": "user",
        "confirmed_at": "synthetic-test-only",
    }
    put(root, "application-config.yaml", config)
    put(root, "requirements.yaml", requirements)
    put(root, "experience-cards.yaml", [card])
    put(root, "research-evidence.yaml", [])
    put(root, "fit-cards.yaml", [])
    draft = f"## Q-01 Process improvement\n{action}<!--c:DIRECT:EXP-01-->\n{outcome}<!--c:DIRECT:EXP-01-->\n"
    (root / "workspace" / "draft-v1.md").write_text(draft, encoding="utf-8")
    records = [
        {
            **{"id": f"CLM-{i:03}", "question_id": "Q-01", "text": text, "label": "DIRECT"},
            "references": [
                {"card_id": "EXP-01", "field": field, "value": text, "card_hash": card_hash(card)}
            ],
        }
        for i, (text, field) in enumerate(
            [(action, "personal_actions.0"), (outcome, "team_result.0")], 1
        )
    ]
    put(root, "claim-map.yaml", {**meta, "claims": records})
    put(
        root,
        "evidence-plan.yaml",
        {
            **meta,
            "coverage": [
                {
                    "id": "Q-01/C-01",
                    "status": "SUFFICIENT",
                    "rationale": "Actual personal action is stated.",
                    "references": [{"card_id": "EXP-01", "field": "personal_actions.0"}],
                    "resolution_owner": "director",
                },
                {
                    "id": "Q-01/C-02",
                    "status": "SUFFICIENT",
                    "rationale": "Actual team usage outcome is stated.",
                    "references": [{"card_id": "EXP-01", "field": "team_result.0"}],
                    "resolution_owner": "director",
                },
            ],
        },
    )
    return root


def review_and_approve(root):
    """Test-only attestations of the exact fixture claims and components."""
    state = validate(root)
    assert state["ok"], state
    meta = {"schema_version": 2, "application_id": state["application_id"]}
    claims = get(root, "claim-map.yaml")["claims"]
    review = {
        **meta,
        "input_hash": state["input_hash"],
        "verdict": "PASS",
        "unresolved_high": [],
        "reviewer": "synthetic-test-reviewer",
        "reviewed_at": "synthetic-test-only",
        "claim_reviews": [
            {
                "id": c["id"],
                "claim_hash": digest(c),
                "verdict": "PASS",
                "rationale": f"Fixture sentence matches {c['references'][0]['field']} exactly.",
            }
            for c in claims
        ],
        "component_reviews": [
            {
                "id": "Q-01/C-01",
                "claim_ids": ["CLM-001"],
                "verdict": "PASS",
                "rationale": "Personal action covered.",
            },
            {
                "id": "Q-01/C-02",
                "claim_ids": ["CLM-002"],
                "verdict": "PASS",
                "rationale": "Team outcome covered.",
            },
        ],
        "quality_checks": {
            k: {
                "verdict": "PASS",
                "rationale": "Synthetic fixture reviewed; no real applicant or portal.",
            }
            for k in QUALITY_CHECKS
        },
    }
    put(root, "review-v1.yaml", review)
    approval = {
        **meta,
        "actor": "user",
        "user_confirmed": True,
        "confirmed_at": "synthetic-test-only",
        "input_hash": state["input_hash"],
        "draft_hash": text_hash((root / "workspace" / "draft-v1.md").read_text()),
        "review_hash": digest(review),
    }
    put(root, "final-approval.yaml", approval)
