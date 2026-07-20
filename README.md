# cover-letter-team

한국 취업 자기소개서(자소서)를 위한 Claude Code 스킬(멀티 에이전트 팀)입니다.
공고를 읽고 그럴듯한 문장을 지어내는 대신, 지원자와의 심층 인터뷰로 실제 경험을
끄집어내고, 그 경험을 근거로만 문장을 쓰도록 강제합니다.

## 핵심 차별점

1. **심층 인터뷰로 소재 발굴** — 문항을 던지자마자 초안을 쓰지 않습니다. Director가
   직접 7단계 인터뷰(범위 안내 → 자유 회상 → 경험카드 구조화 → 공고·문항 매핑 →
   갭 인터뷰 → 검증 질문 → 사용자 게이트)를 진행해, 지원자 본인도 미처 정리하지
   못했던 경험을 함께 구조화합니다.
2. **경험카드·claim-map으로 날조 차단** — 인터뷰에서 확정한 경험은 `experience-cards.yaml`로
   고정되고, 사용자가 승인(`user_confirmed: true`)한 카드만 채택됩니다. Writer가
   쓰는 모든 문장은 `<!--c:LABEL:EXP-NN-->` 형식의 claim 주석으로 경험카드에 연결되며,
   `claim_check.py`가 claim 주석이 달린 모든 주장의 근거 무결성을 기계 검증합니다
   (주석 자체가 누락되지 않았는지는 Reviewer가 검증 3에서 직접 확인합니다).
3. **2계층 AI 티 검증 + 문체 신뢰도** — 표면적 AI 말투(surface_check.py)와 내용
   신호(리뷰어의 3중 검증: AI 티 / 인사담당자 페르소나 / 근거 검증) 두 계층으로
   점검합니다. 동시에 Style Analyst가 사용자의 문체 샘플을 분석해 `style_confidence`를
   명시한 `style-profile.md`를 만들어, 반영된 문체가 지원자 본인의 것인지 신뢰도를
   함께 보고합니다.

## 설치

```bash
git clone https://github.com/djfksjd/cover-letter-team.git cover-letter-team
ln -s "$(pwd)/cover-letter-team" ~/.claude/skills/cover-letter-team
```

이후 **새 Claude Code 세션**에서 "자소서 써줘"라고 말하면 스킬이 자동으로 트리거됩니다.

## 사용법

### 1. 지원 건 폴더 구조

이 스킬은 지원 건마다 **레포 밖에** 별도 폴더를 만들어 작업합니다 (개인정보가 레포에
섞이지 않도록). 구조는 다음과 같습니다.

```
<회사명>_<직무>_<시기>/
├── assets/       ← 이력서, 경험 정리, 문체 샘플 (선택)
├── job/          ← 공고 URL(url.md) 또는 문항 텍스트 (필수)
├── workspace/    ← 중간 산출물 (research.md, interview.md, experience-cards.yaml,
│                    style-profile.md, question-plan.md, draft-v{N}.md, review-v{N}.md)
└── output/       ← 최종 자소서 (*.md + *.docx)
```

폴더가 없는 상태로 시작하면 Director가 위 구조를 안내하고, 사용자 확인 후 `mkdir -p
workspace output`을 실행합니다. `examples/sample-project`에 가상 인물·기업으로 만든
데모 폴더(`job/questions.md`, `assets/이력_요약.md`)가 들어 있으니 구조를 참고하세요.

### 2. 파이프라인 7단계 (요약)

| Phase | 담당 | 내용 |
|---|---|---|
| 0. 입력 분석 | Director | `job/`·`assets/` 스캔, 문체 모드·글자수 기준·블라인드 여부 확인 |
| 1. Researcher | 서브에이전트 | 공고 원문 확보 → `research.md` |
| 2. 심층 인터뷰 | Director (직접) | 7단계 대화형 인터뷰 → `interview.md`, `experience-cards.yaml` — **사용자 게이트 ①: 경험카드 승인** |
| 3. Style Analyst | 서브에이전트 | 문체 샘플 분석 → `style-profile.md` (`style_confidence` 명시) |
| 4. Writer | 서브에이전트 | 승인된 경험카드 기준 초안 작성 → `question-plan.md`, `draft-v{N}.md` |
| 5. Director Review | Director | 결정적 스크립트(표면/중복/근거/글자수/블라인드) + 3중 검증 → `review-v{N}.md`, HIGH 0개까지 최대 3루프 재작성 |
| 6. 산출 | Director | `.docx` 변환, claim 주석 제거본 저장 — **사용자 게이트 ②: 최종 사실 확인** |

전체 오케스트레이션 로직과 각 단계 상세 지침은 `SKILL.md`와 `prompts/`(researcher.md,
interviewer.md, style-analyst.md, writer.md, reviewer.md, ai-tells.md)에 있습니다.

### 3. 사용자 게이트 2곳

- **경험카드 승인 (Phase 2 종료 시)**: 인터뷰로 구조화한 경험카드 중 최소 1개 이상을
  사용자가 직접 확인·승인(`user_confirmed: true`)해야 Writer 단계로 넘어갑니다. 이
  게이트를 통과하지 못한 경험은 자소서에 쓰이지 않습니다.
- **최종 사실 확인 (Phase 6 종료 시)**: 산출 직전, `review-v{final}.md`에 정리된
  INTERPRETIVE(해석·추론) 문장 목록을 사용자에게 보여주고 "모든 문장이 실제로 한
  일이거나 할 법한 말이 맞는지"를 확인받습니다. 이 확인 없이는 완료 처리하지 않습니다.

## 선택 의존성

- **`pip3 install python-docx`** — 최종 산출물을 `.docx`로도 저장하려면 필요합니다
  (`scripts/docx_convert.py`가 사용). 설치하지 않아도 `.md` 산출물은 정상적으로
  생성됩니다.
- **차단 우회 스킬 (예: `insane-search`)** — 그리팅, 원티드, 자사 채용페이지처럼
  크롤러 차단이 걸린 공고 URL을 Researcher가 직접 못 읽을 때 도움이 됩니다. 없어도
  동작에는 지장이 없으며, 이 경우 공고 URL 대신 문항 텍스트를 `job/`에 붙여넣어
  진행하면 됩니다.

## 개인정보 안내

- 지원 건 폴더(`<회사명>_<직무>_<시기>/`)는 **이 레포 밖에** 생성됩니다. 레포 안에는
  실제 지원자의 개인정보가 들어가지 않습니다.
- 인터뷰 원문(`interview.md`), 이력서, 경험 정리 등은 사용자의 로컬 파일 시스템에만
  존재하며, 이 프로젝트나 외부로 전송·저장되지 않습니다.
- `docs/lessons.md`(운영 교훈 기록)에는 사용자 문장·경험·기업명 등 개인정보를 절대
  기록하지 않습니다. 기록 전에는 반드시 사용자에게 내용을 먼저 보여주고 승인을
  받습니다.

## 철학

> 최적화 대상은 AI 흔적의 부재가 아니라, 지원자가 모든 문장을 "내가 실제로 한
> 일"이라고 확인할 수 있는가이다.

이 스킬은 표면적으로 자연스러운 문장을 만드는 것 자체를 목표로 삼지 않습니다.
**탐지기(AI 텍스트 탐지 도구) 점수를 올리기 위한 최적화는 금지합니다.** 탐지기를
피하려고 문장을 일부러 어색하게 바꾸는 것도, 반대로 탐지기를 통과할 정도로만
매끄럽게 다듬는 것도 목적이 아닙니다. 모든 문장은 경험카드에 근거해야 하고,
지원자 본인이 "이건 내가 실제로 한 일이거나 할 법한 말이다"라고 확인할 수 있어야
합니다. 이 확인 절차(경험카드 승인, 최종 사실 확인)가 이 프로젝트가 만든 산출물을
신뢰할 수 있게 만드는 유일한 기준입니다.

## 라이선스

[MIT](LICENSE)
