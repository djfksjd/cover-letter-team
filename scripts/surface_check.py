"""Advisory style checks; never an AI detector or an automatic rejection gate."""

import re
import statistics
import sys
from pathlib import Path

from charcount import CLAIM_RE

RULES = [
    ("em-dash", re.compile(r"[—–]")),
    ("세미콜론", re.compile(r";")),
    ("번역투", re.compile(r"함에 있어|을 통해 .{0,10}을 도모|그럼에도 불구하고")),
    ("대칭구문", re.compile(r"단순히 .{1,15}가 아니라|뿐만 아니라")),
    ("나열식", re.compile(r"첫째[,、]|둘째[,、]|셋째[,、]")),
    ("상투적 마무리", re.compile(r"인재가 되겠습니다|보답하겠습니다|이바지하겠습니다")),
]
SENT_SPLIT = re.compile(r"(?<=[.!?다요])\s+")


def find_issues(text: str, language: str = "ko") -> list:
    text = CLAIM_RE.sub("", text)
    issues = []
    symmetric_hits = []
    for n, line in enumerate(text.splitlines() or [text], 1):
        for rule, rx in RULES:
            if not language.startswith("ko") and rule != "em-dash":
                continue
            m = rx.search(line)
            if m:
                if rule == "대칭구문":
                    # 문서 전체 누적 2회 이상일 때만 보고 (1회는 허용, ai-tells.md 참고)
                    symmetric_hits.append({"line": n, "rule": rule, "match": m.group()})
                else:
                    issues.append({"line": n, "rule": rule, "match": m.group()})
    if len(symmetric_hits) >= 2:
        issues.extend(symmetric_hits)
    return issues


def sentence_length_stats(text: str) -> dict:
    text = CLAIM_RE.sub("", text)
    sents = [s for s in SENT_SPLIT.split(text.strip()) if s]
    lens = [len(s) for s in sents]
    if len(lens) < 2:
        return {"mean": float(lens[0]) if lens else 0.0, "stdev": 0.0}
    return {"mean": statistics.mean(lens), "stdev": statistics.stdev(lens)}


def main(path: str, language: str = "ko") -> int:
    text = Path(path).read_text(encoding="utf-8")
    issues = find_issues(text, language)
    stats = sentence_length_stats(text)
    for i in issues:
        print(f"L{i['line']} [{i['rule']}] {i['match']}")
    print(f"문장 길이 평균 {stats['mean']:.0f}자, 표준편차 {stats['stdev']:.0f}")
    print("Advisory only: punctuation/rhythm do not establish AI authorship or submission failure.")
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:3]))
