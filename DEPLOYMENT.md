# Local Deployment

## Current Local URL

- Streamlit app: http://localhost:8501
- Verified at: 2026-06-18 16:44:51 +09:00

## Run Command

```powershell
cd C:\AI_Agent\ex16
..\.venv\Scripts\python.exe -m streamlit run app.py --server.port 8501 --server.headless true
```

## Verification

- Local HTTP check: `200 OK`
- Codex right-side browser: opened at `http://localhost:8501`
- Visible sections:
  - 개인 일정 관리 AI 에이전트
  - PC workspace
  - 상단 검색, 날짜 선택, 일/주/월 보기 전환, 알림, 프로필
  - 좌측 미니 캘린더와 메뉴
  - 중앙 일/주/월 캘린더와 일정 조회/변경
  - 우측 AI 일정 입력, 직접 등록, 중요한 일정 알림, 우선순위 추천
  - 신규 PC DB: `data/personal_assistant_pc.db`
