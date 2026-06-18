# Agent별 1차 병렬 작업 지시서

## 목적

총괄 기획서 `planner_agent/SERVICE_PLAN.md`를 기준으로 각 Agent가 자기 역할에 맞는 1차 작업을 병렬로 진행한다. 각 Agent는 자기 폴더의 `PHASE1_TASKS.md`를 기준으로 산출물을 관리한다.

## 공통 작업 규칙

- 먼저 `GUIDELINES.md`와 `PHASE1_TASKS.md`를 읽고 작업한다.
- 기능을 바꾸면 관련 테스트 또는 최소 실행 검증을 남긴다.
- API 키가 없어도 로컬 SQLite 기반 기능은 동작해야 한다.
- 외부 API 연동 실패가 앱 전체 실패로 이어지지 않게 한다.
- 작업 완료 후 변경 요약과 검증 결과를 기록한다.

## 병렬 진행 순서

| Agent | 1차 작업 | 주요 산출물 |
| --- | --- | --- |
| planner_agent | 서비스 범위와 완료 기준 확정 | `SERVICE_PLAN.md` |
| design_agent | B2B 대시보드 디자인 가이드와 UI 개선안 작성 | `DESIGN_SPEC.md` |
| lead_dev_agent | 코드 구조와 통합 체크리스트 작성 | `PHASE1_TASKS.md` |
| calendar_agent | SQLite/Google Calendar 책임 범위 정리 | `PHASE1_TASKS.md` |
| ai_agent | 자연어 파서와 LLM 연동 기준 정리 | `PHASE1_TASKS.md` |
| notification_agent | 중요/임박 알림 정책 정리 | `PHASE1_TASKS.md` |
| priority_agent | 우선순위 점수화 기준 정리 | `PHASE1_TASKS.md` |
| qa_agent | 테스트와 검증 체크리스트 정리 | `PHASE1_TASKS.md` |

## 1차 통합 기준

- 각 Agent의 산출물이 총괄 기획서와 충돌하지 않는다.
- 사용자 예시 명령이 계속 통과한다.
- UI 변경은 디자인 가이드의 색상, 레이아웃, 컴포넌트 원칙을 따른다.
- 커밋 전 `pytest`를 실행한다.

