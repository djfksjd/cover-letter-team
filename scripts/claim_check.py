"""claim-map 무결성 검사 — 모든 사실 주장의 근거 추적이 유효한지 기계 검증."""
import re
import sys

LABELS = {"DIRECT", "PARAPHRASE", "DERIVED", "INTERPRETIVE", "UNSUPPORTED"}
CLAIM = re.compile(r"<!--c:([A-Z]+):([A-Za-z0-9,\-]+)-->")
CARD_ID = re.compile(r"^- id: (EXP-\d+)", re.MULTILINE)
CONFIRMED = re.compile(r"user_confirmed: (true|false)")


def parse_card_ids(yaml_text: str) -> dict:
    """PyYAML 없이 id/user_confirmed만 추출 (표준 라이브러리 제약)."""
    out = {}
    blocks = re.split(r"(?=^- id: )", yaml_text, flags=re.MULTILINE)
    for b in blocks:
        m = CARD_ID.search(b)
        if m:
            c = CONFIRMED.search(b)
            out[m.group(1)] = bool(c and c.group(1) == "true")
    return out


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
                errs.append(f"존재하지 않는 근거 ID: {i}")
            elif not cards[i]:
                errs.append(f"미승인 카드 사용: {i} (user_confirmed: false)")
    return errs


def main(draft_path: str, cards_path: str) -> int:
    cards = parse_card_ids(open(cards_path, encoding="utf-8").read())
    errs = check_claims(open(draft_path, encoding="utf-8").read(), cards)
    for e in errs:
        print(e)
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
