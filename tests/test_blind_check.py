import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "scripts"))
from blind_check import find_pii

def test_detects_university():
    assert any(p["category"] == "학교명" for p in find_pii("한국대학교 재학 중"))

def test_detects_age():
    assert any(p["category"] == "나이" for p in find_pii("1999년생으로서"))
    assert any(p["category"] == "나이" for p in find_pii("만 27세입니다"))

def test_detects_family():
    assert any(p["category"] == "가족" for p in find_pii("아버지의 가르침으로"))

def test_clean_text_passes():
    assert find_pii("데이터 분석 동아리에서 활동했습니다.") == []

def test_detects_gender_with_age():
    assert any(p["category"] == "성별" for p in find_pii("저는 27세 남성입니다."))

def test_no_false_positive_third_person_gender():
    assert not any(p["category"] == "성별" for p in find_pii("여성 고객 대상 서비스를 기획했습니다."))

def test_detects_hometown_place_first():
    assert any(p["category"] == "출신지" for p in find_pii("부산 출신입니다."))
