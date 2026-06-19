# AI Scheduler Agent 업무 분담

## 1. 목적

`AI Scheduler`는 개인 일정 관리 웹서비스 AI 에이전트다. 현재 PC용 Streamlit 웹 UI, SQLite 기반 일정 저장소, 주/일/월 캘린더 화면, AI 입력 작업 영역, Google Calendar 연동 확장점을 갖고 있다.

앞으로의 개발은 외부 사이트와 프로그램에서 일정을 수집하고, AI가 일정 확인/정리/수집 실행을 보조하는 방향으로 확장한다. 이 문서는 그 확장을 전제로 개발 agent의 책임 범위와 적용 원칙을 정의한다.

## 2. 전체 처리 흐름

1. 사용자가 웹 UI 또는 AI 명령으로 일정 확인/등록/변경/수집을 요청한다.
2. `ai_agent`가 자연어 의도를 해석하고 필요한 action을 계획한다.
3. 외부 데이터가 필요하면 `collector_agent`가 수집 대상을 식별하고, `integration_agent`가 연결 방식과 인증 조건을 관리한다.
4. 수집된 일정 후보는 표준 일정 스키마로 정규화된다.
5. `calendar_agent`가 SQLite 및 Google Calendar 동기화 규칙에 맞게 저장/변경한다.
6. `priority_agent`와 `notification_agent`가 우선순위와 알림 상태를 계산한다.
7. `design_agent`가 사용자가 이해하기 쉬운 화면 상태와 피드백을 설계한다.
8. `qa_agent`가 테스트와 로컬 배포 검증을 수행하고, `planner_agent`가 이력과 산출물을 정리한다.

## 3. Agent별 책임

| Agent | 핵심 책임 | 주요 산출물 |
| --- | --- | --- |
| `planner_agent` | 전체 기획, 우선순위, 작업 이력, agent 분장 | 기획서, 로드맵, HISTORY |
| `design_agent` | PC/Mobile UI/UX, 화면 배치, 디자인 시스템 | 화면 설계서, UI 가이드 |
| `lead_dev_agent` | 코드 구조, 앱 통합, 배포, 공통 규칙 | 아키텍처 문서, 통합 코드 |
| `calendar_agent` | 일정 도메인, SQLite CRUD, Google Calendar sync | 일정 모델, 저장소, sync 로직 |
| `collector_agent` | 외부 사이트/프로그램 일정 수집, 후보 정규화 | 수집 파이프라인, 후보 데이터 |
| `integration_agent` | 외부 API/OAuth/adapter 관리 | connector 규격, 인증 설정 |
| `ai_agent` | 자연어 명령, AI action planning, LLM 연동 | intent parser, action executor |
| `notification_agent` | 중요 일정 알림, 임박 일정 감지 | reminder rule, alert widget |
| `priority_agent` | 우선순위 추천, 점수화, productivity score | scoring rule, 추천 설명 |
| `security_agent` | 개인정보, 권한, 토큰, 감사 원칙 | 보안 체크리스트, consent flow |
| `qa_agent` | 테스트, 회귀 검증, 로컬 배포 확인 | 테스트 결과, 배포 확인 로그 |

## 4. 외부 연동 적용 원칙

- 모든 외부 연동은 adapter 단위로 구현한다.
- adapter는 `fetch`, `normalize`, `deduplicate`, `sync_status` 단계를 분리한다.
- 사용자의 계정 정보, API key, OAuth token은 `.env` 또는 안전한 credential store를 사용하고 git에 저장하지 않는다.
- 외부 사이트 화면 자동화가 필요한 경우, 우선 공식 API를 검토하고 API가 없을 때만 브라우저 자동화를 검토한다.
- 외부 데이터를 바로 확정 일정으로 저장하지 않고, 가능한 한 "일정 후보"로 보여준 뒤 사용자가 승인할 수 있게 한다.
- 중복 일정은 제목, 날짜, 시작/종료 시간, 출처, 외부 event id를 기준으로 비교한다.
- 수집 실패는 조용히 무시하지 않고 사용자에게 원인과 다음 행동을 알려준다.

## 5. AI 기능 적용 원칙

- AI는 일정 등록/조회/변경/수집 요청을 action으로 변환한다.
- 날짜/시간이 모호하면 KST 기준으로 해석하되, 확정이 어려운 경우 사용자 확인을 요청한다.
- AI가 외부 사이트나 프로그램에서 수집 작업을 실행할 때는 대상, 범위, 저장 여부를 명확히 표시한다.
- LLM 응답은 일정 도메인 스키마로 검증한 뒤 저장소에 전달한다.
- AI 추천은 근거를 짧게 표시해야 하며, 사용자가 수정할 수 있어야 한다.

## 6. 현재 PC UI 기준

- 서비스 제목은 `AI Scheduler`로 유지한다.
- 좌측은 메뉴, view 선택, mini calendar, integration 상태를 담당한다.
- 중앙은 일/주/월 캘린더 콘텐츠를 담당한다.
- 우측 또는 하단 작업 영역은 AI 일정 입력, 검색, Google Calendar 가져오기, 직접 등록 기능을 담당한다.
- Streamlit 기본 상단 UI가 업무 화면을 가리지 않도록 숨김/레이아웃 CSS를 유지한다.

## 7. 작업 완료 기준

- 관련 agent 문서가 갱신되어야 한다.
- 기능 변경은 pytest 또는 최소 import 검증을 통과해야 한다.
- 로컬 배포는 `http://localhost:8501`에서 확인해야 한다.
- 작업 이력은 KST 기준 시작/종료/소요시간과 산출물을 포함해야 한다.
- 작업 단위가 끝나면 commit 후 원격 repo에 push한다.
