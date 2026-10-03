# cover-letter-team

한국·해외 기업의 자기소개서와 지원 문항, 영어 cover letter·supporting statement 등을
실제 경험과 현재 공고에 맞춰 작성하는 에이전트 팀 스킬입니다. Director가 지원자와
인터뷰하고 Researcher·Evidence Planner·Style Analyst·Writer·Reviewer 역할을 조율합니다.

회사 국적만으로 글의 형식을 정하지 않습니다. **채용 국가·법인·직무·경력 수준·작성
언어·문서 유형**을 분리하므로 외국계 한국 지사의 한국어 문항과 한국 기업 해외 법인의
영문 지원서를 각각 다룹니다. 회사가 정해지지 않았다면 경험부터 정리할 수 있습니다.

## 핵심 기능

- **정보 부족 판단과 필요한 질문:** 문항의 필수 하위요소를 근거 필드에 대응합니다.
  결정적 누락·근거 기반 충분성 판단·선택 개선을 구분하며, 이미 답한 질문은 반복하지
  않습니다. ‘모름/경험 없음/건너뛰기’를 존중합니다. 숫자가 없어도 산출물·전후 변화·
  피드백으로 구체화할 수 있습니다.
- **경험·회사 사실·지원 의사 분리:** EXP는 실제 경험, RSH는 출처 확인된 회사 사실,
  FIT는 본인이 말한 지원 이유·포부입니다. claim-map은 본문을 정확한 카드 필드·값·
  해시와 연결합니다. 승인 ID가 있다는 이유만으로 새 행동·수치·주도권을 만들지 않습니다.
- **현재 요건과 최근 변화:** 현재 공식 공고를 우선하며 최근 3년을 초기 탐색 범위로
  비교 가능한 법인·직무·전형 자료를 확인합니다. 과거 자료 부재는 ‘비교 불가’입니다.
  합격 사례는 관련성이 있을 때만 조사하고 서류/최종 합격·편집·출처 한계를 구분합니다.
- **엄격한 내용 완성도 심사:** 사실·형식 PASS와 정보의 깊이를 별도로 평가합니다.
  문항별 STRONG/ADEQUATE/THIN/NOT_READY와 실제 문장 근거를 기록하고 THIN/NOT_READY는
  최종 산출을 차단합니다. 행동 이름만 있고 실제 내용·이유·과정을 알 수 없으면 필요한
  사실을 추가 확인합니다. ADEQUATE를 최고 품질이라고 표시하지 않습니다.
- **언어·문서별 문체:** 한국어 종결체·시제·어휘와 영어 능동태·역할 동사·철자 체계·
  편지 형식을 구분합니다. 샘플이 없으면 기본 문체로 진행하고 모방 신뢰도를 표시합니다.
  정상적인 문장부호나 공식 최소가 없는 낮은 채움 비율은 자동 탈락 기준이 아닙니다.
- **변경 감지와 승인 후 산출:** 카드 변경은 이전 카드 승인을, 요건/본문 변경은 리뷰와
  최종 승인을 무효화합니다. 명시된 파일 조건은 미승인 미리보기로 검토하고, 실제
  사용자 최종 확인 후에만 MD/DOCX를 내보냅니다. 검토한 DOCX는 같은 바이트로 출력합니다.

## 설치

Python 3.11 이상이 필요합니다. YAML은 PyYAML, DOCX는 python-docx를 사용합니다.

```bash
git clone https://github.com/djfksjd/cover-letter-team.git
cd cover-letter-team
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
mkdir -p ~/.claude/skills
ln -s "$(pwd)" ~/.claude/skills/cover-letter-team
```

새 Claude Code 세션에서 `자소서 써줘` 등으로 사용합니다. 다른 스킬 호스트에서는
이 폴더의 `SKILL.md`를 로드합니다. 역할 위임이 허용되지 않는 환경에서는 메인 에이전트가
역할별로 수행하며 독립 리뷰를 했다고 주장하지 않습니다. 모델 이름을 고정하지 않습니다.

## 사용 예

- “회사 아직 안 정했어. 경험부터 정리해줘.” → `experience_inventory`, 공고 요구 없이 경험 정리.
- “이 공고의 한국어 자소서 두 문항을 써줘.” → 현행 문항·직무 확인, 필요한 경험 인터뷰.
- “영국 법인의 500단어 supporting statement를 써줘.” → 필수 criteria별 근거, 영어 논증 문서.
- “미국 회사 영어 cover letter를 내 문체로 써줘.” → 실제 공고·문체 샘플 출처 확인, 편지 형식.

공고 URL·문항·이력서를 이미 제공했다면 그 자료에서 확보 가능한 정보를 다시 묻지
않습니다. 맞춤 제출에 필요한 대상/원문이 없으면 부족 항목만 요청합니다. 회사가 없는
범용 초안은 `DRAFT_FOR_CUSTOMIZATION`이며 맞춤 제출 완료로 표시하지 않습니다.

## 지원 건 폴더와 진행

실제 지원자의 자료는 **이 레포 밖**에 지원 건마다 별도 폴더로 저장합니다.

```text
<지원건>/
├── assets/                   # 이력서·경험·문체 샘플, 선택
├── job/                      # 현행 공고·문항·지원 안내
├── workspace/
│   ├── application-config.yaml
│   ├── requirements.yaml
│   ├── research.md / research-history.yaml
│   ├── interview.md
│   ├── experience-cards.yaml / research-evidence.yaml / fit-cards.yaml
│   ├── evidence-plan.yaml / question-plan.md / style-profile.md
│   ├── draft-v1.md / claim-map.yaml
│   ├── preview/              # 미승인 검토용 파일, 필요할 때
│   ├── review-v1.md / review-v1.yaml
│   └── final-approval.yaml   # 실제 최종 확인 후 작성
└── output/                   # 승인된 application.md/.docx와 manifest
```

흐름은 입력 → 현재 요건 조사 → 경험/접점 인터뷰 → 근거 계획 → 문체 → 작성 → 리뷰 →
최종 확인 → 산출입니다. 정보 부족은 `NEEDS_USER_INPUT`, 해결하지 못한 초안은
`DRAFT_WITH_ISSUES`입니다. 기본 3회 리뷰 상한에 도달해도 문제가 남으면 제출용으로
내보내지 않습니다. 경험 정리 모드는 `EXPERIENCE_ORGANIZED`에서 끝납니다.

카드·요건·claim·리뷰·승인 스키마와 v1 이관 절차는 [파일 계약](references/contracts.md),
[내용 완성도 심사](references/content-quality.md),
질문 정책은 [입력·갭 정책](references/intake-and-gaps.md)에 있습니다. v1 프로젝트를
파일 존재만으로 승인하지 않으며 v2 메타데이터와 현재 요건·리뷰를 명시적으로 갱신합니다.

## 검증 도구

스킬 폴더에서 아래 명령을 실행합니다. `APPLICATION_DIR`은 지원 건 절대경로로 바꿉니다.

```bash
python scripts/readiness_check.py APPLICATION_DIR
python scripts/validate_application.py APPLICATION_DIR --draft workspace/draft-v1.md
python scripts/preview_application.py APPLICATION_DIR --draft workspace/draft-v1.md
python scripts/validate_application.py APPLICATION_DIR --draft workspace/draft-v1.md --review workspace/review-v1.yaml
python scripts/export_application.py APPLICATION_DIR --draft workspace/draft-v1.md --review workspace/review-v1.yaml --approval workspace/final-approval.yaml
```

미리보기는 필요한 파일 조건의 검토 단계이며 최종 제출 파일이 아닙니다. 표면 문체·
중복·블라인드 도구는 의심 후보를 제시하는 조언용입니다. 공식 금지 정보와 문맥을
Reviewer가 대조합니다. 길이는 공백 포함/제외 문자·단어·UTF-8 바이트·UTF-16 단위를
지원하지만 실제 포털 카운터는 별도로 확인해야 합니다.

**기계 검사와 의미 검토는 다릅니다.** 코드는 중복/잘못된 YAML·무효 ID·미승인/오래된
근거·claim-map 불일치·문항 누락·공식 분량 오류·새 숫자 토큰·오래된 리뷰/승인을
차단합니다. 같은 숫자로 다른 성과를 만들거나 인과·역할을 바꾼 문장은 실제 근거 대조와
사용자 확인이 필요합니다. 해시는 변경 감지이며 사람의 신원/동의 인증이 아닙니다.

DOCX는 텍스트와 제목을 재추출해 대조합니다. 페이지 수·레이아웃·지원 사이트 업로드·
PDF/HWP 등 다른 요구 형식은 자동 보증하지 않습니다. 해당 조건을 실제 확인하기
전에는 제출 가능 판정을 하지 않습니다. 파일 생성은 지원 사이트 제출과 다릅니다.

## 근거 자료

[문체·문항·직무·파일 가이드](references/writing-guide.md),
[회사별 조사/최근 연도/사례 정책](references/research-policy.md),
[34개 공개 출처와 적용 범위](references/research-sources.md)를 포함합니다.
공고에 명시된 조건, 출처의 일반 권장, 팀의 운영 판단을 구분합니다. 조사 기준일은
2026-10-03이며 새로운 지원에는 현행 공고를 다시 확인합니다.

전 세계 기업·연도·언어를 빠짐없이 조사했다거나 글만으로 합격을 보장한다고 주장하지
않습니다. 내부 PASS는 사실·요건·문체·제출 준비도의 검토 결과이며 합격 확률이 아닙니다.
AI 사용 금지/제한은 실제 고용주 정책을 따릅니다. AI 탐지 회피·타인 경험/문장 복제는
기능에 포함하지 않습니다. 영어 외 언어는 현지 가이드를 추가 확인합니다.

## 테스트와 개발

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m ruff check scripts tests
python -m ruff format --check scripts tests
```

테스트에는 YAML 주석/중복/타입 승인 우회, NONE/중복 DERIVED 근거, 무주석 본문,
새 수치 창작, 필수 하위요소 부족, 개인/팀 의미 검토 한계, 공식 분량, Unicode/줄바꿈
단어수, 변경된 카드/본문/요건/리뷰/최종 승인, 미리보기 파일 변경, 한국어/영어 문서의
검토·산출 흐름이 포함됩니다. 독립 가상 요청 테스트의 범위는 [검증 기록](docs/validation.md)에
있습니다. 별도 심사위원 테스트와 내용 부족 차단 결과는
[엄격 품질 검증](docs/strict-quality-validation.md)에 기록했습니다. 합성 테스트 승인 기록은 실제 지원자의 동의와 구분합니다.

## 개인정보와 한계

이 레포는 스킬·공개 참고 자료·합성 예시/테스트만 저장합니다. workspace/output과
개인 DOCX는 gitignore로 제외되지만 실제 개인정보를 저장소에 넣지 않는 책임을
대체하지는 않습니다. 스킬은 지원자 자료를 검색어·외부 사이트에 보내지 않습니다.
LLM 호스트가 내용을 처리하는 정책은 별도이며 ‘로컬 파일 저장’을 ‘외부 처리 없음’으로
설명하지 않습니다. 운영 교훈에 지원자 문장·경험·기업명·개인정보를 저장하지 않습니다.

MIT License.
