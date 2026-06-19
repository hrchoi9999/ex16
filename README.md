# 개인 일정 관리 웹서비스 AI 에이전트

ex16 실습 과제: Personal Assistant Agent.

## 목표

Python 기반 웹서비스에서 자연어 명령과 폼 입력으로 개인 일정을 관리한다. 기본 저장소는 SQLite이며, API 키와 인증 파일이 준비되면 Google Calendar와 Gemini 또는 OpenAI Platform 연동을 확장할 수 있다.

## 주요 기능

- 일정 등록
- 일정 조회
- 일정 변경
- 중요한 일정 알림
- 우선순위 추천

## 실행

```powershell
cd C:\AI_Agent\ex16
..\.venv\Scripts\python.exe -m streamlit run app.py
```

## 예시 명령

```text
다음 주 화요일 오후 2시에 회의 등록해줘.
```

예상 응답:

```text
일정을 등록했습니다.

- 제목: 회의
- 날짜: 2026-06-23
- 시간: 오후 2시
```

## 구조

- `app.py`: Streamlit 웹 UI
- `personal_assistant/`: 일정 관리 도메인 코드
- `agents/`: 역할별 Agent 작업 원칙과 가이드
- `tests/`: 핵심 파서와 저장소 테스트

## Agent 기획 문서

- 총괄 서비스 기획서: `agents/planner_agent/SERVICE_PLAN.md`
- 1차 병렬 작업 지시서: `agents/PHASE1_PARALLEL_WORK.md`
- 디자인 스펙: `agents/design_agent/DESIGN_SPEC.md`

## API 연동 메모

현재 앱은 API 키 없이도 SQLite로 동작한다. Google Calendar 동기화는 운영자가 Google Cloud OAuth 클라이언트를 한 번 설정하면 활성화된다. 일반 사용자는 키 파일을 입력하지 않고 화면의 Google 로그인 버튼으로 권한 동의만 진행한다. Gemini/OpenAI 자연어 파싱은 API 키가 없을 때 규칙 기반 파서로 대체된다.

Google Calendar 연동 방식:

- 운영자 설정: `GOOGLE_OAUTH_CLIENT_ID`/`GOOGLE_OAUTH_CLIENT_SECRET` 또는 `GOOGLE_OAUTH_CLIENT_SECRET_FILE`을 서버 환경에 보관한다.
- redirect URI: 로컬 개발 기본값은 `http://localhost:8501/`이며, Google Cloud OAuth 클라이언트의 승인된 리디렉션 URI와 정확히 같아야 한다.
- 사용자 화면: 앱에서 `Google 로그인 열기`를 눌러 Google 로그인 URL을 생성하고, Google 로그인/Calendar 권한 동의를 진행한다.
- 서비스 계정 방식은 개인 캘린더 로그인 UX가 아니라 공유 캘린더/서버 간 연동용으로만 사용한다.

관리자/사용자 역할과 최초 실행, 회원 가입, 회원 로그인 프로세스는 `agents/integration_agent/GOOGLE_OAUTH_PROCESS.md`에서 관리한다.
