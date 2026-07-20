import sys, pathlib
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
