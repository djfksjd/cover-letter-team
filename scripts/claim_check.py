"""Claim annotation syntax/reference gates. Semantic truth requires Reviewer."""

import argparse
import re
from pathlib import Path

from contracts import read_cards

LABELS = {"DIRECT", "PARAPHRASE", "DERIVED", "INTERPRETIVE", "UNSUPPORTED", "NONFACTUAL"}
CLAIM = re.compile(r"<!--c:([A-Z]+):([A-Za-z0-9,\-]+)-->")
SUSPECT = re.compile(r"<!--\s*c\s*:[\s\S]*?(?:-->|$)", re.IGNORECASE)
_NAMESPACES = {
    "EXP": ("user_confirmed", "미승인 카드 사용"),
    "RSH": ("verified", "미검증 리서치 사실 사용"),
    "FIT": ("user_confirmed", "미승인 회사 접점 카드 사용"),
}


def _parse_ids(yaml_text, prefix, gate_field):
    return {
        key: card[gate_field] for key, card in read_cards(yaml_text, prefix, gate_field).items()
    }


def parse_card_ids(yaml_text):
    return _parse_ids(yaml_text, "EXP", "user_confirmed")


def parse_evidence_ids(yaml_text):
    return _parse_ids(yaml_text, "RSH", "verified")


def parse_fit_ids(yaml_text):
    return _parse_ids(yaml_text, "FIT", "user_confirmed")


def check_claims(md_text, cards):
    errs = []
    for candidate in SUSPECT.finditer(md_text):
        m = CLAIM.fullmatch(candidate.group())
        if not m:
            errs.append("잘못된 claim 마커 구문")
            continue
        label, raw = m.groups()
        ids = raw.split(",")
        if label not in LABELS:
            errs.append(f"무효 라벨: {label}")
            continue
        if label == "UNSUPPORTED":
            errs.append("UNSUPPORTED 주장 존재 — 삭제 또는 보충 인터뷰 필요")
            continue
        if label == "NONFACTUAL":
            if ids != ["NONE"]:
                errs.append(
                    "NONFACTUAL must use NONE; Reviewer verifies no factual assertion is hidden"
                )
            continue
        if "NONE" in ids or not all(re.fullmatch(r"(?:EXP|RSH|FIT)-\d{2,}", i) for i in ids):
            errs.append(f"유효 근거 최소 1개 필요: {raw}")
        if len(set(ids)) != len(ids):
            errs.append(f"중복 근거 ID: {raw}")
        if label == "DERIVED" and len(set(ids) - {"NONE"}) < 2:
            errs.append("DERIVED: 서로 다른 근거 2개 이상 필요")
        for key in ids:
            if key == "NONE":
                continue
            if key not in cards:
                errs.append(f"존재하지 않는 근거 ID: {key}")
            elif not cards[key]:
                errs.append(f"{_NAMESPACES[key.split('-')[0]][1]}: {key}")
    return errs


def main(draft_path, cards_path, evidence_path=None, fit_path=None):
    try:
        cards = {}
        for path, prefix, gate in [
            (cards_path, "EXP", "user_confirmed"),
            (evidence_path, "RSH", "verified"),
            (fit_path, "FIT", "user_confirmed"),
        ]:
            if path is not None:
                cards.update(_parse_ids(Path(path).read_text(encoding="utf-8"), prefix, gate))
        errs = check_claims(Path(draft_path).read_text(encoding="utf-8"), cards)
    except (ValueError, OSError) as exc:
        print(f"Input error: {exc}")
        return 2
    for error in errs:
        print(error)
    print(
        "Scope: annotation syntax and IDs only; validate_application.py checks coverage/freshness, Reviewer checks meaning."
    )
    return 1 if errs else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("draft")
    parser.add_argument("cards")
    parser.add_argument("evidence", nargs="?")
    parser.add_argument("fit", nargs="?")
    args = parser.parse_args()
    raise SystemExit(main(args.draft, args.cards, args.evidence, args.fit))
