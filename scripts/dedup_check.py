"""문항 간 유사 문장 검사 — 같은 소재·문장의 재사용을 잡는다."""
import re
import sys
from difflib import SequenceMatcher

from charcount import split_questions, CLAIM_RE

SENT_SPLIT = re.compile(r"(?<=[.!?다요])\s+")


def _sentences(body: str) -> list:
    body = CLAIM_RE.sub("", body)
    return [s.strip() for s in SENT_SPLIT.split(body.strip()) if len(s.strip()) >= 10]


def find_duplicates(md_text: str, threshold: float = 0.8) -> list:
    qs = split_questions(md_text)
    out = []
    for i in range(len(qs)):
        for j in range(i + 1, len(qs)):
            for s1 in _sentences(qs[i][1]):
                for s2 in _sentences(qs[j][1]):
                    r = SequenceMatcher(None, s1, s2).ratio()
                    if r >= threshold:
                        out.append({"q1": qs[i][0], "q2": qs[j][0],
                                    "s1": s1, "s2": s2, "ratio": r})
    return out


def main(path: str) -> int:
    dups = find_duplicates(open(path, encoding="utf-8").read())
    for d in dups:
        print(f"[{d['q1']}] ↔ [{d['q2']}] 유사도 {d['ratio']:.2f}\n  {d['s1']}\n  {d['s2']}")
    return 1 if dups else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
