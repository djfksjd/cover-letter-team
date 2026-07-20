import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "scripts"))
from claim_check import parse_card_ids, check_claims

CARDS = """- id: EXP-01
  user_confirmed: true
- id: EXP-02
  user_confirmed: false"""

def test_parse_card_ids():
    ids = parse_card_ids(CARDS)
    assert ids == {"EXP-01": True, "EXP-02": False}

def test_valid_claim_passes():
    assert check_claims("인터뷰 5건을 진행했습니다.<!--c:DIRECT:EXP-01-->",
                        parse_card_ids(CARDS)) == []

def test_unsupported_is_flagged():
    errs = check_claims("매출을 2배로 올렸습니다.<!--c:UNSUPPORTED:NONE-->",
                        parse_card_ids(CARDS))
    assert any("UNSUPPORTED" in e for e in errs)

def test_unconfirmed_card_is_flagged():
    errs = check_claims("발표에서 2위를 했습니다.<!--c:DIRECT:EXP-02-->",
                        parse_card_ids(CARDS))
    assert any("미승인" in e for e in errs)

def test_derived_needs_two_ids():
    errs = check_claims("분석과 실행을 병행했습니다.<!--c:DERIVED:EXP-01-->",
                        parse_card_ids(CARDS))
    assert any("DERIVED" in e for e in errs)

def test_unknown_id_is_flagged():
    errs = check_claims("동아리를 이끌었습니다.<!--c:DIRECT:EXP-99-->",
                        parse_card_ids(CARDS))
    assert any("EXP-99" in e for e in errs)
