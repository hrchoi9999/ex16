# Agent 작업 분담

각 Agent는 자기 폴더의 `GUIDELINES.md`를 기준으로 작업한다. 구현은 작은 단위로 나누고, 한 작업 단위가 끝나면 테스트 후 커밋/푸시한다.

## 역할

- `planner_agent`: 요구사항, 일정 관리 UX, 작업 우선순위 정의
- `design_agent`: 화면 구성, UX 흐름, 사용자 문구, 접근성 점검 담당
- `lead_dev_agent`: 개발 총괄, 코드 구조, 통합 기준, 커밋/푸시 흐름 담당
- `calendar_agent`: SQLite 일정 CRUD와 Google Calendar 연동 담당
- `ai_agent`: 자연어 명령 파싱, Gemini/OpenAI 연동 담당
- `notification_agent`: 중요한 일정 알림과 임박 일정 탐지 담당
- `priority_agent`: 우선순위 추천 규칙과 점수화 담당
- `qa_agent`: 테스트, 실행 검증, 회귀 확인 담당

## 1차 병렬 작업 흐름

1. 모든 Agent는 먼저 `planner_agent/SERVICE_PLAN.md`를 읽는다.
2. 다음으로 `PHASE1_PARALLEL_WORK.md`에서 전체 병렬 작업 흐름을 확인한다.
3. 각 Agent는 자기 폴더의 `GUIDELINES.md`와 `PHASE1_TASKS.md`를 기준으로 작업한다.
4. `design_agent`는 추가로 `DESIGN_SPEC.md`의 디자인 프롬프트와 토큰을 반드시 따른다.
5. 작업이 끝나면 `qa_agent` 기준에 따라 검증하고, `lead_dev_agent`가 커밋/푸시 흐름을 확인한다.
