"""Advisory style checks; never an AI detector or an automatic rejection gate.

규칙 일부는 im-not-ai(Humanize KR, MIT, epoko77-ai/im-not-ai @ b37e020)의 한국어 패턴
분류와 실측 보정(문서 밀도 임계, 사람이 더 쓰는 표현의 기본 보존)을 자기소개서에 맞게
옮긴 것이다. 출처·채택 이유는 references/naturalness-patterns.md.

목적은 읽는 사람이 막히는 상투·직역 표현 후보를 찾는 것이다. 탐지기 점수를 낮추거나
AI 사용을 숨기는 도구가 아니며, 결과만으로 HIGH를 주지 않는다(prompts/reviewer.md).

사용:
  surface_check.py DRAFT [LANG]              # 사람용 출력, 항상 exit 0
  surface_check.py DRAFT [LANG] --json       # 리뷰 기록용
  surface_check.py --compare OLD NEW [LANG]  # 수정본이 새 패턴을 만들었거나 숫자를 바꿨는지
"""

import json
import re
import statistics
import sys
from pathlib import Path

from charcount import CLAIM_RE

# (id, 이름, 심각도, 정규식, 문서 내 최소 횟수). 최소 횟수 미만이면 보고하지 않는다.
# 심각도는 im-not-ai의 S1(한 번도 눈에 띔)·S2(반복되면 눈에 띔)·S3(약함) 의미를 따른다.
# 기존 규칙 이름(em-dash·번역투·대칭구문 등)은 이전 리뷰 기록과의 호환을 위해 유지한다.
RULES = [
    ("L-01", "em-dash", "S3", re.compile(r"[—–]"), 1),
    ("L-02", "세미콜론", "S3", re.compile(r";"), 1),
    ("L-03", "번역투", "S1", re.compile(r"함에 있어|을 통해 .{0,10}을 도모|그럼에도 불구하고"), 1),
    ("L-04", "대칭구문", "S1", re.compile(
        r"단순히 .{1,15}가 아니라|뿐만 아니라|것이 아니라|것은 아닙니다|인가, .{1,15}인가"), 2),
    ("L-05", "나열식", "S2", re.compile(r"첫째[,、]|둘째[,、]|셋째[,、]"), 1),
    ("L-06", "상투적 마무리", "S2", re.compile(r"인재가 되겠습니다|보답하겠습니다|이바지하겠습니다"), 1),
    # --- im-not-ai 계열 (ID 뒤 괄호는 원 분류 ID) ---
    ("A-03", "~에 있어(서) 직역", "S1", re.compile(r"(?<!함)에 있어(서)?(?! ?[가-힣]*니다)"), 1),
    ("A-07", "'가지고 있다' 직역", "S2", re.compile(r"가지고 있(습니다|다|는|어)"), 2),
    ("A-08", "이중 피동", "S1", re.compile(r"되어(지|진|집|졌)"), 1),
    ("A-19", "이중 조사", "S2", re.compile(r"(에서의|에로의|으로의|에의|으로부터의)"), 2),
    ("A-21", "'단순한 X를 넘어' 상승 구문", "S2", re.compile(r"단순(히|한) [^.\n]{1,20}(을|를)? ?넘어"), 1),
    ("A-22", "'~은 분명합니다' 평가 술어", "S2", re.compile(r"(명확|분명)(합니다|하다|했습니다)"), 2),
    ("D-01", "결산 접속어 반복", "S2", re.compile(r"결론적으로|따라서|이를 통해|그러므로|요약하면|정리하자면"), 4),
    ("D-02", "의의 과장", "S1", re.compile(r"시사하는 바가 크|주목할 만(하|합|한)|매우 중요(하|합|한)"), 1),
    ("D-03", "열거 도입구", "S2", re.compile(r"크게 (두|세|네) 가지|다음과 같(습니다|은|이)"), 1),
    ("D-06", "결말 공식 '~할 때입니다'", "S2", re.compile(r"할 때입니다|할 시점입니다|할 순간입니다"), 1),
    ("D-07", "변환 공식 'X를 넘어 Y로'", "S2", re.compile(r"(을|를) 넘어 [^.\n]{1,15}(으)?로"), 2),
    ("D-08", "분열문 '중요한 것은 ~'", "S2", re.compile(r"(필요한|중요한) 것은|핵심은|관건은"), 2),
    ("D-10", "도치 결산 '~하는 이유입니다'", "S2", re.compile(r"(는|한|던) 이유(입니다|다)\."), 2),
    ("D-14", "사전 은유", "S2", re.compile(r"잠식|청사진|적신호|경고등|신호탄|움켜쥐|뿌리내리|짓누르"), 1),
    ("G-02", "이중 완곡", "S2", re.compile(
        r"가능성이 있을 수 있|보여질 수 있|ㄹ 수도 있을 것|할 수도 있을 것"), 1),
    ("I-03", "'~다는 것입니다' 결말", "S2", re.compile(r"다는 (것|뜻)(입니다|이다)"), 3),
    ("J-01", "볼드 강조", "S2", re.compile(r"\*\*[^*\n]+\*\*"), 3),
]

# 연결어미 직후 쉼표(im-not-ai C-11, KatFish 기반). 개별 쉼표는 정상이므로 문서 밀도로만 본다.
ENDING_COMMA = re.compile(r"[가-힣]+(?:고|며|지만|면서|아서|어서|해서|는데),")
ENDING_COMMA_NOUNS = {"공고", "재고", "광고", "최고", "참고", "사고", "경고", "창고", "원고", "신고"}
ENDING_COMMA_MIN, ENDING_COMMA_STRONG = 3, 6

# '-적 N' 추상 체인(F-5). 원래 '적'으로 끝나는 명사는 제외한다.
JEOK_CHAIN = re.compile(r"([가-힣]{1,6})적 [가-힣]")
JEOK_NOUNS = {"목", "실", "업", "성", "흔", "기", "지", "국", "누", "표", "행", "궤", "개인", "직"}
JEOK_MIN = 3

# 사람 글에서 더 자주 쓰여 기본 보존하는 표현(im-not-ai A-1·A-2·A-11 실측 보정).
# 한 문단에 몰릴 때만 후보로 낸다.
PARAGRAPH_CLUSTER = [
    ("A-01", "'~에 대해' 문단 밀집", re.compile(r"에 대(해|해서|한|하여)"), 3),
    ("A-02", "'~를 통해' 문단 밀집", re.compile(r"(을|를) 통(해|하여)"), 3),
    ("A-11", "'~을 위해' 문단 밀집", re.compile(r"(을|를) 위(해|하여|한)"), 3),
]
# 같은 가능형 반복(A-10). 단정 전환이 아니라 배치·형태 분산이 처방이다.
CAN_REPEAT = ("A-10", "'~할 수 있' 반복", re.compile(r"[ㄹ을] 수 있|할 수 있"), 4)

QUOTE_PAIR = re.compile(r"[\"“][^\"”\n]{1,40}[\"”]|'[^'\n]{1,30}'|‘[^’\n]{1,30}’")
QUOTE_MIN = 5  # J-2: 따옴표 강조 5회+

SENT_SPLIT = re.compile(r"(?<=[.!?다요])\s+")
NUMBER = re.compile(r"\d[\d,.]*\s?(%|퍼센트|명|개|건|회|시간|분|초|일|주|개월|년|원|만원|억|kW|kWh|V|A|Hz|점|위|등|배)?")


def _clean(text: str) -> str:
    return CLAIM_RE.sub("", text)


def _hits(text: str, rx: re.Pattern) -> list:
    out = []
    for n, line in enumerate(text.splitlines() or [text], 1):
        for m in rx.finditer(line):
            out.append({"line": n, "match": m.group()})
    return out


def find_issues(text: str, language: str = "ko") -> list:
    """후보 목록. 각 항목: id·rule·severity·line·match (+count·threshold)."""
    text = _clean(text)
    korean = language.startswith("ko")
    issues = []
    for rid, name, sev, rx, minimum in RULES:
        if not korean and rid != "L-01":
            continue
        hits = _hits(text, rx)
        if rid.startswith("L-") and rid != "L-04":
            # 이전 버전과 같이 줄당 첫 매치만 보고
            seen = set()
            hits = [h for h in hits if not (h["line"] in seen or seen.add(h["line"]))]
        if rid == "L-04":
            seen = set()
            hits = [h for h in hits if not (h["line"] in seen or seen.add(h["line"]))]
        if len(hits) >= minimum:
            for h in hits:
                issues.append({"id": rid, "rule": name, "severity": sev, "count": len(hits),
                               "threshold": minimum, **h})
    if not korean:
        return issues

    comma_hits = [h for h in _hits(text, ENDING_COMMA)
                  if h["match"].rstrip(",") not in ENDING_COMMA_NOUNS]
    if len(comma_hits) >= ENDING_COMMA_MIN:
        sev = "S1" if len(comma_hits) >= ENDING_COMMA_STRONG else "S2"
        for h in comma_hits:
            issues.append({"id": "C-11", "rule": "연결어미 뒤 쉼표", "severity": sev,
                           "count": len(comma_hits), "threshold": ENDING_COMMA_MIN, **h})

    jeok = [h for h in _hits(text, JEOK_CHAIN)
            if re.match(r"([가-힣]{1,6})적", h["match"]).group(1) not in JEOK_NOUNS]
    if len(jeok) >= JEOK_MIN:
        for h in jeok:
            issues.append({"id": "F-05", "rule": "'-적 N' 추상 체인", "severity": "S2",
                           "count": len(jeok), "threshold": JEOK_MIN, **h})

    line_no = 1
    for para in re.split(r"\n\s*\n", text):
        for rid, name, rx, minimum in PARAGRAPH_CLUSTER:
            ms = list(rx.finditer(para))
            if len(ms) >= minimum:
                issues.append({"id": rid, "rule": name, "severity": "S2", "count": len(ms),
                               "threshold": minimum, "line": line_no,
                               "match": " / ".join(m.group() for m in ms)})
        line_no += para.count("\n") + 2

    rid, name, rx, minimum = CAN_REPEAT
    can = _hits(text, rx)
    if len(can) >= minimum:
        issues.append({"id": rid, "rule": name, "severity": "S2", "count": len(can),
                       "threshold": minimum, "line": can[0]["line"],
                       "match": f"{len(can)}회 — 단정으로 바꾸지 말고 일부 배치만 분산"})

    quotes = _hits(text, QUOTE_PAIR)
    if len(quotes) >= QUOTE_MIN:
        for h in quotes:
            issues.append({"id": "J-02", "rule": "따옴표 강조", "severity": "S2",
                           "count": len(quotes), "threshold": QUOTE_MIN, **h})
    return issues


def rule_counts(text: str, language: str = "ko") -> dict:
    """임계와 무관한 규칙별 원 횟수. --compare의 주입 감지에 쓴다."""
    text = _clean(text)
    counts = {}
    for rid, name, _sev, rx, _min in RULES:
        if language.startswith("ko") or rid == "L-01":
            counts[f"{rid} {name}"] = len(_hits(text, rx))
    if language.startswith("ko"):
        counts["C-11 연결어미 뒤 쉼표"] = len([h for h in _hits(text, ENDING_COMMA)
                                         if h["match"].rstrip(",") not in ENDING_COMMA_NOUNS])
        for rid, name, rx, _m in PARAGRAPH_CLUSTER:
            counts[f"{rid} {name}"] = len(rx.findall(text))
        counts[f"{CAN_REPEAT[0]} {CAN_REPEAT[1]}"] = len(CAN_REPEAT[2].findall(text))
    return counts


def numbers(text: str) -> list:
    return sorted(m.group().strip() for m in NUMBER.finditer(_clean(text)))


def compare(old: str, new: str, language: str = "ko") -> dict:
    """수정본 점검: 원문에 없던 패턴을 새로 만들었나(주입), 숫자·단위가 바뀌었나."""
    a, b = rule_counts(old, language), rule_counts(new, language)
    injected = {k: {"before": a.get(k, 0), "after": v} for k, v in b.items() if v > a.get(k, 0)}
    na, nb = numbers(old), numbers(new)
    lost = [x for x in na if na.count(x) > nb.count(x)]
    added = [x for x in nb if nb.count(x) > na.count(x)]
    return {"injected": injected, "numbers_removed": sorted(set(lost)),
            "numbers_added": sorted(set(added))}


def sentence_length_stats(text: str) -> dict:
    text = _clean(text)
    sents = [s for s in SENT_SPLIT.split(text.strip()) if s]
    lens = [len(s) for s in sents]
    if len(lens) < 2:
        return {"mean": float(lens[0]) if lens else 0.0, "stdev": 0.0}
    return {"mean": statistics.mean(lens), "stdev": statistics.stdev(lens)}


NOTE = ("Advisory only: punctuation/rhythm/phrasing do not establish AI authorship or "
        "submission failure. 후보마다 문맥을 읽고 판단하고, 고칠 때 사실·수치·주장 강도를 바꾸지 않는다.")


def main(path: str, language: str = "ko", as_json: bool = False) -> int:
    text = Path(path).read_text(encoding="utf-8")
    issues = find_issues(text, language)
    stats = sentence_length_stats(text)
    if as_json:
        print(json.dumps({"issues": issues, "sentence_stats": stats, "note": NOTE},
                         ensure_ascii=False, indent=2))
        return 0
    for i in issues:
        extra = f" ({i['count']}회/기준 {i['threshold']})" if i.get("threshold", 1) > 1 else ""
        print(f"L{i['line']} [{i.get('id', '')} {i['rule']}|{i.get('severity', '')}] {i['match']}{extra}")
    s1 = sum(1 for i in issues if i.get("severity") == "S1")
    print(f"후보 {len(issues)}건 (S1 {s1}건) · 문장 길이 평균 {stats['mean']:.0f}자, 표준편차 {stats['stdev']:.0f}")
    print(NOTE)
    return 0


def main_compare(old_path: str, new_path: str, language: str = "ko", as_json: bool = False) -> int:
    res = compare(Path(old_path).read_text(encoding="utf-8"),
                  Path(new_path).read_text(encoding="utf-8"), language)
    if as_json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0
    if not any(res.values()):
        print("수정본이 새 패턴을 만들지 않았고 숫자도 그대로입니다.")
    for k, v in res["injected"].items():
        print(f"[주입] {k}: {v['before']} → {v['after']}")
    if res["numbers_removed"]:
        print("[숫자 사라짐] " + ", ".join(res["numbers_removed"]))
    if res["numbers_added"]:
        print("[숫자 새로 생김] " + ", ".join(res["numbers_added"]) + " — 근거 카드에 있는 값인지 확인")
    print(NOTE)
    return 0


def _cli(argv: list) -> int:
    as_json = "--json" in argv
    args = [a for a in argv if a != "--json"]
    if args and args[0] == "--compare":
        return main_compare(*args[1:4], as_json=as_json)
    return main(*args[:2], as_json=as_json)


if __name__ == "__main__":
    sys.exit(_cli(sys.argv[1:]))
