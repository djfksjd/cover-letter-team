"""블라인드 채용 금지정보 휴리스틱 검사. 의심 라인 보고 — 최종 판단은 사람이 한다."""
import re
import sys

PATTERNS = [
    ("학교명", re.compile(r"[가-힣]+(?:대학교|대학원|고등학교|고교)")),
    ("나이", re.compile(r"만 ?\d{1,2}세|\d{4}년생|[12]\d살")),
    ("성별", re.compile(r"(?:저는|본인은) ?(?:남자|여자|남성|여성)")),
    ("가족", re.compile(r"아버지|어머니|부모님|형제|남매|장남|장녀|막내")),
    ("출신지", re.compile(r"(?:출신|고향)[은는이가]? ?[가-힣]{2,6}")),
]


def find_pii(text: str) -> list:
    out = []
    for n, line in enumerate(text.splitlines() or [text], 1):
        for cat, rx in PATTERNS:
            m = rx.search(line)
            if m:
                out.append({"line": n, "category": cat, "match": m.group()})
    return out


def main(path: str) -> int:
    hits = find_pii(open(path, encoding="utf-8").read())
    for h in hits:
        print(f"L{h['line']} [{h['category']}] {h['match']}")
    if hits:
        print(f"\n금지정보 의심 {len(hits)}건 — 블라인드 채용이면 제거 필요")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
