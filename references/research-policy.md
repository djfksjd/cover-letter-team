# 지원 건별 조사와 변경 이력

관련 작성 지침/공개 정책 출처는 [research-sources](research-sources.md)에 있다.
처음부터 모든 사례를 수집하는 대신 현재 지원서의 요구를 해결한다.

## 출처 우선순위

현재 대상 공식 공고·지원 시스템·첨부·FAQ > 해당 회사 공식 직무/사업 자료 >
명확한 사용자 제공 원문 > 과거 같은 범위 공식 자료 > 신뢰할 수 있는 보조 해설 >
출처·합격 단계가 기록된 사례. 출처 순위만으로 동일 출처의 모든 내용이 현재 사실은 아니다.
같은 법인/직무/채용 회차인지 확인한다. 링크만 있는 것이 아니라 실제 본문·짧은 인용·
위치·검색/접속 날짜·접근 상태를 기록한다. 검색 스니펫은 직접 원문 확인과 구분한다.
날짜 없는 공식 현행 서비스 페이지는 retrieved_at+내용 확인으로 검증할 수 있다.
뉴스는 게시일과 사건일을 구분하며 시점 의존 사실을 재확인한다.

## 최근 몇 년 비교

최근 3년은 기본 초기 탐색 범위인 운영 선택이다. 실제 채용 주기·공개 자료·질문 해석에
따라 2년/5년 등으로 조정하고 이유를 기록한다. 연도를 채우려고 무관한 기업/직무를
섞지 않는다. 동일 법인·직무군·채용 유형·경력 수준·지역을 비교 키로 쓴다. 문항 원문,
하위요소, 단위/최소/최대, 파일 조건, blind/AI 정책, **공개된** 평가 기준을 비교한다.

문항 변경, 분량 변경, 평가 방식 공개 변경은 각자 다른 사건이다. 문항만 바뀌었는데
숨은 평가 가중치도 바뀌었다고 단정하지 않는다. 과거 자료 미확보는 not_comparable,
차이 확인은 confirmed_change, 동일 범위 확인은 no_observed_change로 기록한다.
최신 공식 요건으로 현재 requirements를 만들고 영향받는 계획·claim·본문을 재검토한다.
비교 가능한 자료를 못 찾았어도 현재 요건이 충분하면 작성은 계속할 수 있다.

## 합격 사례의 반대 검토와 조건부 채택

공개 사례는 표본 선택 편향, 서류/최종 합격 혼동, 직무·문항 변경, 첨삭·편집·허위
가능성이 있다. 성과 높은 사람의 글이 그 표현 때문에 합격했다는 인과 증거가 아니다.
문항 해석/구체성 관찰에 도움이 될 때만 3~5개의 관련 사례를 초기 예산으로 검토한다.
중복/무관 사례나 새로운 관찰이 없는 자료는 더 수집하지 않는다. 중요한 불확실성을
해결할 자료가 있으면 예산을 늘리고 이유를 기록한다. 전수/무누락/완벽을 주장하지 않는다.

기록: CASE ID, URL, 접근 상태, 게시/지원 연도, 법인, 직무, 경력 수준, 실제 문항,
합격 단계(screening/final/unknown), 증빙/편집 여부, 비교 가능성, 관찰, 한계.
CASE는 타인 표현/경험의 관찰이며 EXP/RSH/FIT 근거가 아니다. 원문을 저장·복제하기보다
짧은 인용과 자체 요약을 사용한다. 문장·경험·수치 재사용을 하지 않는다.

K-water 2026 일부 전형의 사례 패턴 기반 AI 평가 공개처럼 예외가 있으면 **해당
공고 범위**의 명시 역량·직무 연관성·내용 충실도를 반영한다. 공개 합격 사례가 실제
학습 데이터라고 추정하거나 은닉 점수를 역설계하지 않는다.

## research-history.yaml 계약 (판단용, 기계 합격 게이트 아님)

```yaml
schema_version: 2
application_id: APP-demo
comparison_scope:
  legal_entity: Example Employer
  role_family: operations
  hiring_type: graduate
  career_level: entry
  hiring_country: GB
window: {start_year: 2024, end_year: 2026, reason: initial_search_budget}
comparisons:
  - id: HISTORY-01
    status: not_comparable
    source_urls: []
    observed_change: null
    private_criteria_status: undisclosed
    impact: Current requirements remain authoritative.
cases: []
stop_reason: No comparable previous official posting found.
```

실제 조사 여부·시점·범위를 기록한다. 사례 조사가 필요 없으면 cases: []와 이유를 쓴다.
