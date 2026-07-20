"""claim-map 무결성 검사 — 모든 사실 주장의 근거 추적이 유효한지 기계 검증."""
import os
import re
import sys

LABELS = {"DIRECT", "PARAPHRASE", "DERIVED", "INTERPRETIVE", "UNSUPPORTED"}
CLAIM = re.compile(r"<!--c:([A-Z]+):([A-Za-z0-9,\-]+)-->")
CARD_ID = re.compile(r"^- id: (EXP-\d+)", re.MULTILINE)
CONFIRMED = re.compile(r"user_confirmed: (true|false)")

# 근거 ID 네임스페이스별 (게이트 필드, 게이트 실패 메시지)
_NAMESPACES = {
    "EXP": ("user_confirmed", "미승인 카드 사용"),
    "RSH": ("verified", "미검증 리서치 사실 사용"),
    "FIT": ("user_confirmed", "미승인 회사 접점 카드 사용"),
}


def _parse_ids(yaml_text: str, prefix: str, gate_field: str) -> dict:
    """PyYAML 없이 id/게이트 필드만 추출 (표준 라이브러리 제약)."""
    out = {}
    id_re = re.compile(rf"^- id: ({prefix}-\d+)", re.MULTILINE)
    gate_re = re.compile(rf"{gate_field}: (true|false)")
    blocks = re.split(r"(?=^- id: )", yaml_text, flags=re.MULTILINE)
    for b in blocks:
        m = id_re.search(b)
        if m:
            g = gate_re.search(b)
            out[m.group(1)] = bool(g and g.group(1) == "true")
    return out


def parse_card_ids(yaml_text: str) -> dict:
    return _parse_ids(yaml_text, "EXP", "user_confirmed")


def parse_evidence_ids(yaml_text: str) -> dict:
    """research-evidence.yaml — verified: true인 회사 사실만 통과."""
    return _parse_ids(yaml_text, "RSH", "verified")


def parse_fit_ids(yaml_text: str) -> dict:
    """fit-cards.yaml — user_confirmed: true인 회사 접점만 통과."""
    return _parse_ids(yaml_text, "FIT", "user_confirmed")


def _gate_fail_msg(card_id: str) -> str:
    prefix = card_id.split("-")[0]
    _, msg = _NAMESPACES.get(prefix, ("", "게이트 미통과 ID 사용"))
    return f"{msg}: {card_id}"


def check_claims(md_text: str, cards: dict) -> list:
    errs = []
    for m in CLAIM.finditer(md_text):
        label, ids_raw = m.group(1), m.group(2)
        ids = [i for i in ids_raw.split(",") if i != "NONE"]
        if label not in LABELS:
            errs.append(f"무효 라벨: {label}")
            continue
        if label == "UNSUPPORTED":
            errs.append("UNSUPPORTED 주장 존재 — 삭제 또는 보충 인터뷰 필요")
            continue
        if label == "DERIVED" and len(ids) < 2:
            errs.append(f"DERIVED인데 근거 {len(ids)}개 — 2개 이상 필요: {ids_raw}")
        for i in ids:
            if i not in cards:
                errs.append(f"존재하지 않는 근거 ID: {i} (해당 카드 파일 미제공이면 함께 전달할 것)")
            elif not cards[i]:
                errs.append(_gate_fail_msg(i))
    return errs


def main(draft_path: str, cards_path: str,
         evidence_path: str = None, fit_path: str = None) -> int:
    cards = parse_card_ids(open(cards_path, encoding="utf-8").read())
    if evidence_path and os.path.exists(evidence_path):
        cards.update(parse_evidence_ids(open(evidence_path, encoding="utf-8").read()))
    if fit_path and os.path.exists(fit_path):
        cards.update(parse_fit_ids(open(fit_path, encoding="utf-8").read()))
    errs = check_claims(open(draft_path, encoding="utf-8").read(), cards)
    for e in errs:
        print(e)
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:5]))
