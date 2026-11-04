import sys
import pathlib

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
    assert not any(
        i["rule"] == "대칭구문" for i in find_issues("협업뿐만 아니라 기록도 챙겼습니다.")
    )


def test_symmetric_phrase_flagged_twice():
    text = "협업뿐만 아니라 기록도 챙겼습니다.\n단순히 속도가 아니라 방향을 봤습니다."
    assert sum(1 for i in find_issues(text) if i["rule"] == "대칭구문") == 2


def test_english_semicolon_is_not_a_korean_style_issue():
    assert find_issues("I built the tool; the team adopted it.", "en-GB") == []


def test_style_candidates_do_not_fail_cli(tmp_path):
    from surface_check import main

    path = tmp_path / "draft.md"
    path.write_text("저는 도전했습니다 — 그리고 배웠습니다.")
    assert main(str(path)) == 0


# --- im-not-ai 계열 규칙 (references/naturalness-patterns.md) ---

def _ids(text):
    return {i["id"] for i in find_issues(text)}


def test_translationese_e_isseo_and_double_passive():
    assert "A-03" in _ids("설비 관리에 있어서 기록이 필요했습니다.")
    assert "A-08" in _ids("결과가 판단되어집니다.")


def test_significance_inflation_and_range_climb():
    ids = _ids("안정성은 매우 중요합니다. 단순한 정비를 넘어 예방을 배웠습니다.")
    assert {"D-02", "A-21"} <= ids


def test_human_common_phrases_need_paragraph_cluster():
    # 사람이 더 자주 쓰는 표현: 한두 번은 보존
    assert "A-02" not in _ids("측정을 통해 원인을 찾았습니다. 기록을 통해 공유했습니다.")
    dense = "측정을 통해 찾고 기록을 통해 남기고 회의를 통해 공유했습니다."
    assert "A-02" in _ids(dense)


def test_ending_comma_needs_density():
    assert "C-11" not in _ids("현장을 보고, 원인을 찾았습니다.")
    many = "현장을 보고, 데이터를 모으며, 원인을 찾았지만, 다시 측정해서, 고쳤습니다."
    assert "C-11" in _ids(many)


def test_noun_ending_in_go_is_not_comma_hit():
    assert "C-11" not in _ids("공고, 재고, 광고, 창고를 정리했습니다.")


def test_compare_flags_injection_and_number_change():
    from surface_check import compare
    res = compare("전압을 220V에서 측정했습니다.", "전압을 230V에서 측정함에 있어 매우 중요합니다.")
    assert res["numbers_removed"] == ["220V"] and res["numbers_added"] == ["230V"]
    assert any(k.startswith("D-02") for k in res["injected"])


def test_cli_json_and_compare_exit_zero(tmp_path, capsys):
    from surface_check import _cli
    a = tmp_path / "a.md"; b = tmp_path / "b.md"
    a.write_text("측정했습니다."); b.write_text("측정했습니다.")
    assert _cli([str(a), "ko", "--json"]) == 0
    assert _cli(["--compare", str(a), str(b)]) == 0
