import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "scripts"))
from charcount import count_section, split_questions


def test_count_excludes_claim_comments():
    text = "저는 인터뷰를 진행했습니다.<!--c:DIRECT:EXP-01-->"
    r = count_section(text)
    assert r["with_spaces"] == len("저는 인터뷰를 진행했습니다.")
    assert r["without_spaces"] == len("저는인터뷰를진행했습니다.")


def test_newlines_not_counted_as_chars():
    r = count_section("가나\n다라")
    assert r["with_spaces"] == 4
    assert r["without_spaces"] == 4


def test_split_questions():
    md = "## 문항 1. 지원동기\n본문A\n\n## 문항 2. 성장과정\n본문B"
    qs = split_questions(md)
    assert len(qs) == 2
    assert qs[0][0] == "문항 1. 지원동기"
    assert "본문A" in qs[0][1]


def test_crlf_is_normalized_at_function_boundary():
    assert count_section("가\r\n나") == count_section("가\n나")


def test_english_and_canonical_headings():
    assert (
        len(split_questions("## Question 1. Motivation\nText\n## Question 2. Experience\nOther"))
        == 2
    )
    assert len(split_questions("## Q-01 Motivation\nText\n## Q-02 Experience\nOther")) == 2


def test_portal_units_and_newline_policy():
    from charcount import count_units

    assert count_units("가😀", "utf8_bytes") == 7
    assert count_units("가😀", "utf16_units") == 3
    assert count_units("a\nb", "characters_with_spaces", "include") == 3
    assert count_units("a\nb", "characters_with_spaces", "exclude") == 2
    assert count_units("I built a check-list.", "words") == 4


def test_word_count_preserves_newline_boundaries():
    from charcount import count_units

    for policy in ["include", "exclude"]:
        assert count_units("one\ntwo\n\nthree", "words", policy) == 3
        assert count_units("one\r\ntwo", "words", policy) == 2


def test_newline_words_at_official_maximum():
    from charcount import count_units

    assert count_units("\n".join(["word"] * 501), "words") == 501
