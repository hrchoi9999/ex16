# Agent 작업 분담

각 Agent는 자기 폴더의 `GUIDELINES.md`를 기준으로 작업한다. 구현은 작은 단위로 나누고, 한 작업 단위가 끝나면 테스트 후 커밋/푸시한다.

## 역할

- `planner_agent`: 요구사항, 일정 관리 UX, 작업 우선순위 정의
- `calendar_agent`: SQLite 일정 CRUD와 Google Calendar 연동 담당
- `ai_agent`: 자연어 명령 파싱, Gemini/OpenAI 연동 담당
- `notification_agent`: 중요한 일정 알림과 임박 일정 탐지 담당
- `priority_agent`: 우선순위 추천 규칙과 점수화 담당
- `qa_agent`: 테스트, 실행 검증, 회귀 확인 담당

