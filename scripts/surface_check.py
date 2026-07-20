"""AI 티 표면 검사(계층 1). 필요조건 게이트일 뿐 충분조건이 아니다 — 내용 검사는 reviewer.md."""
import re
import statistics
import sys

RULES = [
    ("em-dash", re.compile(r"[—–]")),
    ("세미콜론", re.compile(r";")),
    ("번역투", re.compile(r"함에 있어|을 통해 .{0,10}을 도모|그럼에도 불구하고")),
    ("대칭구문", re.compile(r"단순히 .{1,15}가 아니라|뿐만 아니라")),
    ("나열식", re.compile(r"첫째[,、]|둘째[,、]|셋째[,、]")),
    ("상투적 마무리", re.compile(r"인재가 되겠습니다|보답하겠습니다|이바지하겠습니다")),
]
SENT_SPLIT = re.compile(r"(?<=[.!?다요])\s+")


def find_issues(text: str) -> list:
    issues = []
    for n, line in enumerate(text.splitlines() or [text], 1):
        for rule, rx in RULES:
            m = rx.search(line)
            if m:
                issues.append({"line": n, "rule": rule, "match": m.group()})
    return issues


def sentence_length_stats(text: str) -> dict:
    sents = [s for s in SENT_SPLIT.split(text.strip()) if s]
    lens = [len(s) for s in sents]
    if len(lens) < 2:
        return {"mean": float(lens[0]) if lens else 0.0, "stdev": 0.0}
    return {"mean": statistics.mean(lens), "stdev": statistics.stdev(lens)}


def main(path: str) -> int:
    text = open(path, encoding="utf-8").read()
    issues = find_issues(text)
    stats = sentence_length_stats(text)
    for i in issues:
        print(f"L{i['line']} [{i['rule']}] {i['match']}")
    print(f"문장 길이 평균 {stats['mean']:.0f}자, 표준편차 {stats['stdev']:.0f}")
    if stats["stdev"] < 8 and stats["mean"] > 0:
        print("경고: 문장 길이가 지나치게 균일함 (리듬 균일 신호)")
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
