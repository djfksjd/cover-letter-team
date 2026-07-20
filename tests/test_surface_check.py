import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "scripts"))
from surface_check import find_issues, sentence_length_stats

def test_detects_em_dash():
    issues = find_issues("저는 도전했습니다 — 그리고 배웠습니다.")
    assert any(i["rule"] == "em-dash" for i in issues)

def test_detects_banned_phrase():
    issues = find_issues("일함에 있어 최선을 다했습니다.")
    assert any(i["rule"] == "번역투" for i in issues)

def test_detects_cliche_ending():
    issues = find_issues("성장하는 인재가 되겠습니다.")
    assert any(i["rule"] == "상투적 마무리" for i in issues)

def test_clean_text_passes():
    assert find_issues("팀원 다섯이 모여 밤새 시제품을 고쳤습니다.") == []

def test_sentence_stats():
    s = sentence_length_stats("짧다. 이 문장은 조금 더 길게 이어집니다. 끝.")
    assert s["stdev"] > 0

def test_sentence_stats_ignore_claim_comments():
    plain = "짧다. 이 문장은 조금 더 길게 이어집니다. 끝."
    annotated = "짧다.<!--c:DIRECT:EXP-01--> 이 문장은 조금 더 길게 이어집니다.<!--c:PARAPHRASE:EXP-02--> 끝."
    assert sentence_length_stats(annotated) == sentence_length_stats(plain)

def test_symmetric_phrase_allowed_once():
    assert not any(i["rule"] == "대칭구문" for i in find_issues("협업뿐만 아니라 기록도 챙겼습니다."))

def test_symmetric_phrase_flagged_twice():
    text = "협업뿐만 아니라 기록도 챙겼습니다.\n단순히 속도가 아니라 방향을 봤습니다."
    assert sum(1 for i in find_issues(text) if i["rule"] == "대칭구문") == 2
