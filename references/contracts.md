# v2 파일 계약과 검사 범위

이 계약은 내부 사실/제출 준비도 검사다. 실제 합격 점수나 의미 검증 알고리즘이 아니다.
YAML 중복 키/ID, 문자열 "true", 빈 ID, 잘못된 타입은 오류다. 기존 v1 프로젝트는 원문과
카드를 유지하되 아래 메타데이터와 요건/claim/리뷰를 작성하고 다시 확인한다. 과거 승인을
자동 이식하지 않는다. 각 지원 건의 application_id는 모든 파일/카드에서 일치해야 한다.

## 설정과 요건

`workspace/application-config.yaml` (아래는 가상 지원 건):

```yaml
schema_version: 2
application_id: APP-example-001
mode: targeted_application # experience_inventory/general_draft는 검토용, 제출 검사 제외
market_entry: international # UI 경로; 규칙은 아래 실제 맥락으로 결정
employer_origin: KR
hiring_country: GB
output_language: en-GB
document_type: supporting_statement # question_answers/cover_letter/personal_statement/selection_criteria
career_level: entry
style_mode: 기본
ending_style: not_applicable # ko는 합쇼체/평서체
blind_hiring: null # true/false/null; 실제 범위를 Researcher가 기록
ai_policy: unknown # allowed/restricted/prohibited/unknown
job_identity:
  legal_entity: Example Employer UK
  title: Operations Analyst
  job_id: JOB-example
  posting_url: null
  source_status: user_provided # official_current/user_provided
```

`workspace/requirements.yaml`:

```yaml
schema_version: 2
application_id: APP-example-001
questions:
  - id: Q-01
    prompt: Explain how you meet the essential criteria.
    source_locator: User supplied instructions, paragraph 1
    components:
      - id: C-01
        text: Evidence of process improvement
        mandatory: true
        source_status: user_provided # explicit/user_provided/inferred
    length:
      unit: words # characters_with_spaces/characters_without_spaces/utf8_bytes/utf16_units
      minimum: null # 없는 최소를 만들지 않음
      maximum: 500
      newline_policy: exclude # include/exclude
      count_status: approximate # portal_verified면 실제 포털 대조 확인 필요
```

공식 의무 조건으로 추정(inferred) 역량을 기록하지 않는다. 편지/연속 논증은 Q-01 한
섹션, 문항형은 여러 Q. words는 공백 분리 근사값, utf8_bytes는 UTF-8 바이트,
utf16_units는 JavaScript 계열 카운터 근사다. 특수문자·줄바꿈·하이픈·포털 인코딩에 따라
차이가 난다. 공식 포털 확인이 없으면 approximate로 표시한다. 검사 분량은 claim 주석을 제거하고
문단 내부 줄바꿈을 공백으로 연결한 실제 제출 본문 기준이다. MD와 DOCX의 본문 의미·분량을
맞추며 문단 사이 줄바꿈 포함 정책은 공고를 따른다. 페이지·파일 크기·양식·
blind/AI 상세 조건은 research/requirements의 추가 필드로 기록하고 Reviewer가 직접 검토한다.

## 카드

EXP/RSH/FIT는 각각 별도 YAML 리스트다. 없으면 `[]`가 유효하다. 모든 카드:

```yaml
- id: EXP-01
  schema_version: 2
  application_id: APP-example-001
  event_id: EVT-01
  personal_actions: [Created a checklist for the team.]
  team_result: [The team used the checklist during handover.]
  precision: {}
  user_confirmed: false
  approval: null
```

EXP의 상세 내용 필드는 interviewer 참조. FIT는 company_fact_ids, user_connection,
connection_origin(preexisting/application_research), intended_contribution, evidence를
기록한다. RSH는 claim/quote/url/legal_entity/source_type/retrieved_at/published_at를
기록하며 gate는 verified다. source_type은 공식/기사/제3자 등 출처 성격, published_at는
확인 못 하면 null. RSH의 검증은 출처·법인·현재성·인용 범위를 실제 대조한 판단이다.

실제 EXP/FIT 사용자 확인 후에만 gate를 true로 바꾸고 다음을 기록한다:

```yaml
approval:
  content_hash: <card_hash 결과>
  actor: user # RSH 검증은 researcher
  confirmed_at: '2026-10-03T09:00:00+09:00'
```

해시는 신원 인증이 아니라 내용 변경 감지다. 에이전트는 사용자가 확인한 것으로
꾸며 기록하지 않는다. 카드 해시는 gate와 approval를 제외한 전체 JSON 정규화 SHA-256이다.
계산은 설치된 scripts의 `contracts.card_hash(card)`를 사용한다. 내용 변경 후 false로
돌리고 변경 부분을 다시 확인한다. 미승인 카드도 보존할 수 있지만 Writer가 쓰지 못한다.

## 요건-근거 계획

`workspace/evidence-plan.yaml`:

```yaml
schema_version: 2
application_id: APP-example-001
coverage:
  - id: Q-01/C-01
    status: SUFFICIENT
    rationale: The confirmed checklist action and handover outcome address the required criterion.
    references:
      - {card_id: EXP-01, field: personal_actions.0}
      - {card_id: EXP-01, field: team_result.0}
    resolution_owner: director
    ask: null
```

상태와 질문 규칙은 intake-and-gaps 참조. readiness_check는 매핑·필드·승인 존재를
검사한다. SUFFICIENT 문맥 판단은 Planner의 기록이며 이후 Reviewer가 본문에서 재검토한다.

## 본문과 claim-map

초안은 canonical `## Q-01 제목` 순서만 사용한다. 부록·Draft 제목·중첩 # 헤딩은
금지. 각 주장 문장/절에 마커를 붙이고 비사실 인사말/전환/소제목은 NONFACTUAL:NONE.
텍스트는 직전 마커/문항 시작부터 다음 마커 직전까지의 문자열을 strip한 값이다.
여러 사실 문장을 한 span에 묶지 않았는지는 Reviewer가 검토한다.

`workspace/claim-map.yaml`:

```yaml
schema_version: 2
application_id: APP-example-001
claims:
  - id: CLM-001
    question_id: Q-01
    text: I created a checklist for the team.
    label: PARAPHRASE
    references:
      - card_id: EXP-01
        field: personal_actions.0 # dict key/list index의 dot 경로
        value: Created a checklist for the team.
        card_hash: <해당 카드 내용 해시>
```

NONFACTUAL은 references: []이며 Reviewer가 사실 주장/의사를 숨기지 않았는지 확인한다.
게이트·ID·approval는 근거 필드로 사용할 수 없다. 숫자 토큰이 참조 필드에 없으면
차단하지만, 같은 숫자로 다른 단위·역할·인과를 만든 것은 의미 검토에서 잡아야 한다.
계산 숫자는 확인된 계산 근거 필드가 먼저 있어야 한다. DIRECT/PARAPHRASE를 구분해도
스크립트가 문장 의미 보존을 자동 증명하는 것은 아니다.

## 리뷰와 최종 승인

`validate_application.py --draft ...`의 input_hash/claim_hashes를 확인한다. input_hash는
config, requirements, 카드 전체, evidence-plan, claim-map, 본문을 묶는다.

`workspace/review-v1.yaml`:

```yaml
schema_version: 2
application_id: APP-example-001
input_hash: <검사 출력>
reviewer: independent-reviewer # 동일 컨텍스트면 director-same-context로 한계 표시
reviewed_at: '2026-10-03T09:10:00+09:00'
verdict: PASS
unresolved_high: []
claim_reviews:
  - id: CLM-001
    claim_hash: <검사 출력의 CLM-001 해시>
    verdict: PASS
    rationale: Compare actual sentence, evidence field, role, precision and meaning here.
component_reviews:
  - id: Q-01/C-01
    verdict: PASS
    claim_ids: [CLM-001]
    rationale: Explain how those claims satisfy the original required component.
quality_checks:
  factual_consistency: {verdict: PASS, rationale: Actual review reason required.}
  role_and_causality: {verdict: PASS, rationale: Actual review reason required.}
  precision_and_privacy: {verdict: PASS, rationale: Actual review reason required.}
  relevance_and_specificity: {verdict: PASS, rationale: Actual review reason required.}
  language_and_voice: {verdict: PASS, rationale: Actual review reason required.}
  submission_policy: {verdict: PASS, rationale: Actual employer policy and remaining file/portal checks addressed.}
```

위 이유는 형식 예시다. 실제 출력에는 문장과 근거를 대조한 이유를 써야 하며 그대로 복사하지 않는다.

`workspace/final-approval.yaml`는 **실제 사용자 최종 확인 후** 작성한다:

```yaml
schema_version: 2
application_id: APP-example-001
actor: user
user_confirmed: true
confirmed_at: '2026-10-03T09:15:00+09:00'
input_hash: <리뷰 검사의 입력 해시>
draft_hash: <리뷰 검사의 본문 해시>
review_hash: <리뷰 검사의 리뷰 해시>
```

리뷰/승인 기록이 있다고 자동으로 사람이 확인했다는 것을 증명하지 않는다. 스킬이
실제 대화 확인을 지켜야 하고 코드는 그 기록이 최신 입력에 대응하는지 검사한다.
export_application.py만 승인 후 산출에 사용한다. docx_convert.py는 승인 게이트가
없는 저수준 개발 도구이며 그 출력 자체를 제출 가능이라고 표시하지 않는다.

## 검사 단계

readiness_check: 요건-카드 정보 충분성 → EVIDENCE_READY/NEEDS_USER_INPUT.
validate_application: 형식+필드+해시 → DRAFT_VALIDATED, --review → READY_FOR_USER_REVIEW,
--approval(리뷰 필수) → APPROVED_FOR_EXPORT. export_application → EXPORTED.
실패한 입력·미해결 HIGH·상한 도달 초안은 DRAFT_WITH_ISSUES. 검사 결과는 민감 원문을
가능한 한 출력하지 않으며 오류 해결에는 지원 건 로컬 파일을 직접 대조한다.


## 미리보기와 파일 리뷰

명시된 파일 조건에는 requirements 최상위 `submission: {file_review_required: true}`를
기록한다. preview_application.py는 workspace/preview/application.docx와 미승인
manifest를 만든다. 실제 조건 확인 후 review-vN.yaml에 다음을 추가한다:

```yaml
file_reviews:
  - path: workspace/preview/application.docx
    sha256: <미리보기 실제 파일 SHA-256>
    verdict: PASS
    rationale: Actual visual/file checks and employer requirements confirmed here.
```

기계는 파일 해시/현재 본문/리뷰 결합을 검사하며 시각 판단은 사람이 또는 가능한 뷰어로
수행한다. export는 검토된 DOCX 바이트를 복사하고 파일 해시를 manifest에 남긴다.
파일 조건이 없고 file_reviews가 비었으면 새 DOCX를 만들며 layout_status는 requires_visual_check다.
PDF/HWP 같은 다른 요구 형식은 자동 지원한다고 주장하지 않는다. 외부 변환/검토 절차가
확보되기 전 지원 형식으로 제출 가능하다고 표시하지 않는다.
