import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "scripts"))
from dedup_check import find_duplicates

MD_DUP = """## 문항 1. 지원동기
사용자 인터뷰를 8건 진행하며 요구를 파악했습니다.

## 문항 2. 협업 경험
사용자 인터뷰를 8건 진행하며 요구를 파악했습니다."""

MD_OK = """## 문항 1. 지원동기
온보딩 개선을 제안해 이탈률을 낮췄습니다.

## 문항 2. 협업 경험
갈등 상황에서 회의록을 먼저 정리해 논점을 좁혔습니다."""

def test_detects_cross_question_duplicate():
    dups = find_duplicates(MD_DUP)
    assert len(dups) == 1
    assert dups[0]["ratio"] >= 0.8

def test_distinct_content_passes():
    assert find_duplicates(MD_OK) == []
