# Agent 작업 분담

이 폴더는 `AI Scheduler` 개발을 여러 agent 책임 영역으로 나누어 관리한다.
각 agent는 자기 폴더의 `GUIDELINES.md`, `ROLE_AND_PRINCIPLES.md`, 작업 지시 문서를 기준으로 움직이며, 작업 결과는 총괄 agent가 이력과 배포 상태로 정리한다.

## 현재 기준

- PC용 일정 관리 웹서비스를 우선 개발한다.
- 현재 구현은 Streamlit 기반 PC UI, SQLite 로컬 저장소, 일정 CRUD, 주/일/월 캘린더 화면, AI 입력 작업 영역, Google Calendar 연동 확장점을 포함한다.
- 앞으로는 Google Calendar뿐 아니라 외부 사이트, 업무 프로그램, 파일, 메일, 메신저 등에서 일정을 수집하고 정리하는 기능을 추가한다.
- AI는 사용자의 자연어 명령을 해석하고, 일정 확인/등록/변경/수집 실행을 보조하는 실행 layer로 확장한다.

## 핵심 문서

- 전체 역할 분담: `AGENT_WORK_ALLOCATION.md`
- 업그레이드 실행 계획: `UPGRADE_EXECUTION_PLAN.md`
- 업그레이드 backlog: `UPGRADE_BACKLOG.md`
- 총괄 기획서: `planner_agent/SERVICE_PLAN.md`
- 작업 이력: `planner_agent/HISTORY.md`
- PC 디자인 기준: `design_agent/PC_DESIGN_SPEC.md`
- 재시작 기준: `../PROJECT_RESTART.md`

## Agent 목록

- `planner_agent`: 총괄 기획, 범위 관리, 작업 이력, agent 간 업무 분장
- `design_agent`: PC/Mobile UI/UX, 화면 구조, 디자인 시스템, 접근성
- `lead_dev_agent`: 개발 총괄, 아키텍처, 코드 통합, 배포 흐름
- `calendar_agent`: 일정 도메인, SQLite CRUD, Google Calendar 동기화
- `collector_agent`: 외부 사이트/프로그램에서 일정 후보 수집 및 정규화
- `integration_agent`: 외부 API, OAuth, adapter contract, connector 품질 관리
- `ai_agent`: 자연어 명령 해석, AI action planning, Gemini/OpenAI 연동
- `notification_agent`: 중요한 일정 알림, 마감 임박 표시, reminder 정책
- `priority_agent`: 우선순위 추천, 점수화, 생산성 지표
- `security_agent`: 개인정보/토큰/권한/감사 로그 원칙
- `qa_agent`: 테스트, 회귀 검증, 로컬 배포 확인

## 운영 원칙

1. 작업 시작 시 총괄 agent가 범위와 담당 agent를 먼저 정리한다.
2. 외부 연동 기능은 `collector_agent`, `integration_agent`, `security_agent`가 함께 승인 기준을 정한다.
3. 일정 데이터의 최종 저장/변경은 `calendar_agent`의 도메인 규칙을 통과해야 한다.
4. AI가 실행하는 작업은 사용자가 이해할 수 있는 계획과 결과 메시지를 남겨야 한다.
5. 개인정보, 인증 토큰, 외부 계정 데이터는 코드와 git에 직접 저장하지 않는다.
6. 작업 단위가 끝나면 테스트/배포 확인 후 commit 및 `hrchoi9999/ex16` 원격 push를 수행한다.

## 업그레이드 작업 원칙

1. 신규 기능 목록은 먼저 `UPGRADE_BACKLOG.md`에 등록한다.
2. `planner_agent`가 기능별 주 담당/협업 agent를 지정한다.
3. 각 agent는 자기 폴더의 `UPGRADE_TASKS.md`에 작업 범위와 완료 기준을 관리한다.
4. `qa_agent`는 모든 개발 산출물에 대해 문서, 코드, 테스트, UI, 데이터, 보안, 배포 gate를 확인한다.
5. 기능 구현이 완료되면 `planner_agent/HISTORY.md`에 KST 기준 작업 이력을 기록한다.
