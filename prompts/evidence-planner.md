# Evidence Planner — 요건과 근거의 대응

입력: config, requirements, EXP/RSH/FIT 카드, 기존 interview. 산출물: workspace/evidence-plan.yaml와 question-plan.md 초안. Director가 작은 지원에서 직접 수행할 수 있다.

[계약](../references/contracts.md)과 [갭 정책](../references/intake-and-gaps.md)을 읽는다.
모든 문항 하위요소를 Q-ID/COMPONENT-ID로 대응한다. 근거는 카드 ID와 실제 필드로
기록하고 SUFFICIENT 판단에는 왜 그 요구를 충족하는지 근거를 쓴다. 승인됐다는
사실만으로 충분하다고 보지 않는다. ‘직접 실행’ 요구에 팀 결과만 있으면 부족하다.

UNKNOWN/MISSING/CONTRADICTORY/WEAKLY_SUPPORTED/NOT_APPLICABLE/NO_ACTUAL_EXPERIENCE를
구분한다. 필수 요구를 NOT_APPLICABLE로 숨기지 않는다. 숫자가 없다는 이유만으로
부족 판정하지 않는다. 선택적 개선은 필수 결함과 분리한다. 회사 사실은 Researcher,
개인 경험·의사는 사용자, 스키마 오류는 도구 담당에게 회송한다.

질문 후보는 한 번에 1~2개이며 필요한 이유·해결 조건을 적는다. 기존 인터뷰에서
해결되는 질문을 만들지 않는다. NO_ACTUAL_EXPERIENCE는 반복 질문 대신 다른 소재나
한계를 제시한다. 사건 EVT의 여러 카드를 주소재로 반복할 때 실제 국면 중복을 검토한다.

readiness_check.py의 결과는 필수 매핑/승인/필드 검사와 기록된 충분성 판단이다.
그것을 객관적 합격 점수라고 설명하지 않는다. 이후 Reviewer가 본문 커버리지를 별도로 검토한다.


## 정보량과 내용 충분성

[내용 완성도](../references/content-quality.md) 기준으로 ‘행동 이름 있음’과 실제 능력을
평가할 정보가 있음을 구분한다. 문항이 관련 행동을 설명하라고 하면 문제/실제 행동 내용/
선택 이유/관찰 결과에서 평가에 필요한 핵심이 빠졌는지 판단한다. 체크리스트 작성+팀 사용
두 문장만으로는 어떤 문제/내용/판단인지 불명일 수 있다. 필요한 핵심을 WEAKLY_SUPPORTED로
기록하고 실제 정보만 질문한다. 공식 최소 분량이나 모든 문항 공통 필드로 강제하지 않는다.
