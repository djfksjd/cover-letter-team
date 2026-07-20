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

RSH = """- id: RSH-01
  verified: true
- id: RSH-02
  verified: false"""

FIT = """- id: FIT-01
  user_confirmed: true
- id: FIT-02
  user_confirmed: false"""

def test_parse_evidence_ids():
    from claim_check import parse_evidence_ids
    assert parse_evidence_ids(RSH) == {"RSH-01": True, "RSH-02": False}

def test_parse_fit_ids():
    from claim_check import parse_fit_ids
    assert parse_fit_ids(FIT) == {"FIT-01": True, "FIT-02": False}

def test_verified_rsh_claim_passes():
    from claim_check import parse_evidence_ids
    cards = {**parse_card_ids(CARDS), **parse_evidence_ids(RSH)}
    assert check_claims("이 회사는 신입 기획자 멘토링 제도를 운영합니다.<!--c:DIRECT:RSH-01-->",
                        cards) == []

def test_unverified_rsh_is_flagged():
    from claim_check import parse_evidence_ids
    cards = {**parse_card_ids(CARDS), **parse_evidence_ids(RSH)}
    errs = check_claims("이 회사는 업계 1위입니다.<!--c:DIRECT:RSH-02-->", cards)
    assert any("RSH-02" in e and "미검증" in e for e in errs)

def test_unconfirmed_fit_is_flagged():
    from claim_check import parse_fit_ids
    cards = {**parse_card_ids(CARDS), **parse_fit_ids(FIT)}
    errs = check_claims("입사 후 온보딩 개선을 맡고 싶습니다.<!--c:INTERPRETIVE:FIT-02-->", cards)
    assert any("FIT-02" in e for e in errs)

def test_rsh_id_without_evidence_file_is_flagged():
    errs = check_claims("이 회사는 멘토링 제도를 운영합니다.<!--c:DIRECT:RSH-01-->",
                        parse_card_ids(CARDS))
    assert any("RSH-01" in e for e in errs)
