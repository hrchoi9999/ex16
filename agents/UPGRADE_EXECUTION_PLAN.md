# AI Scheduler Upgrade Execution Plan

## 1. 목적

현재 개발된 `AI Scheduler` 일정관리 프로그램에 신규 기능을 단계적으로 추가하기 위한 업그레이드 진행 기준이다.

아직 구체 기능 목록은 확정되지 않았으므로, 이 문서는 기능 목록이 도착했을 때 바로 분석, agent 배정, 개발, QA, 배포로 이어지도록 준비된 운영 문서다.

## 2. 현재 개발 기준

- 앱 이름: `AI Scheduler`
- 실행 환경: `C:\AI_Agent\.venv`
- 프로젝트 경로: `C:\AI_Agent\ex16`
- 로컬 배포 URL: `http://localhost:8501`
- 주요 기술: Python, Streamlit, SQLite, Google Calendar API extension, Gemini/OpenAI extension
- 현재 UI 방향: PC 우선, 좌측 메뉴/중앙 캘린더/작업 영역 기반

## 3. 업그레이드 진행 단계

### Step 1. 기능 접수

사용자가 추가할 기능 목록을 전달하면 `planner_agent`가 각 기능을 다음 기준으로 정리한다.

- 기능 목적
- 사용자 시나리오
- 화면 영향도
- 데이터 모델 영향도
- 외부 연동 필요 여부
- AI 필요 여부
- 보안/권한 고려사항
- 테스트 난이도

### Step 2. Agent 배정

기능별로 주 담당 agent와 협업 agent를 지정한다.

- UI/UX 변경: `design_agent`
- 코드 구조/통합: `lead_dev_agent`
- 일정 저장/조회/동기화: `calendar_agent`
- 외부 수집: `collector_agent`
- API/OAuth/connector: `integration_agent`
- 자연어 명령/AI 실행: `ai_agent`
- 중요 일정 알림: `notification_agent`
- 우선순위/추천: `priority_agent`
- 개인정보/권한: `security_agent`
- 테스트/품질관리: `qa_agent`

### Step 3. Agent별 작업 MD 작성

각 agent는 자기 폴더의 `UPGRADE_TASKS.md`에 다음 항목을 관리한다.

- 담당 기능
- 작업 범위
- 산출물
- 의존 agent
- 완료 기준
- QA 확인 항목
- 진행 상태

### Step 4. 개발 및 통합

`lead_dev_agent`가 브랜치/커밋 단위와 통합 순서를 관리한다.

- 작은 기능 단위로 구현한다.
- DB schema 변경은 migration 또는 compatibility 방안을 먼저 정리한다.
- 외부 API 연동은 mock 가능한 adapter로 구현한다.
- AI 응답은 schedule schema 검증을 통과한 뒤 저장한다.

### Step 5. QA 및 배포

`qa_agent`가 품질 기준을 통과한 산출물만 배포 대상으로 승인한다.

- pytest 실행
- import 검증
- 주요 UI 흐름 확인
- `http://localhost:8501` 로컬 배포 확인
- 변경 기능별 acceptance criteria 확인

## 4. 기능 분석 템플릿

| ID | 기능명 | 목적 | 주 담당 | 협업 Agent | UI 영향 | DB 영향 | 외부 연동 | AI 영향 | 보안 영향 | 우선순위 | 상태 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TBD-001 | 기능 목록 입력 대기 | 사용자가 전달할 신규 기능 분석 예정 | planner_agent | TBD | TBD | TBD | TBD | TBD | TBD | TBD | 대기 |

## 5. 업그레이드 원칙

- 사용자 일정 데이터의 신뢰성과 안전성을 우선한다.
- 외부 사이트/프로그램 연동은 공식 API를 우선 검토한다.
- 수집한 외부 일정은 확정 저장 전 후보 상태로 표시한다.
- AI 실행 결과는 사용자에게 근거와 결과를 명확히 보여준다.
- 모든 작업 단위는 문서, 구현, 테스트, 배포 확인, commit/push까지 하나의 완료 흐름으로 본다.
