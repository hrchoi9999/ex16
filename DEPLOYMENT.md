# Local Deployment

## Current Local URL

- Streamlit app: http://localhost:8501
- Verified at: 2026-06-18 16:10:25 +09:00

## Run Command

```powershell
cd C:\AI_Agent\ex16
..\.venv\Scripts\python.exe -m streamlit run app.py --server.port 8501 --server.headless true
```

## Verification

- Local HTTP check: `200 OK`
- Codex right-side browser: opened at `http://localhost:8501`
- Visible sections:
  - AI 일정 관리
  - 좌측 월간 캘린더와 메뉴
  - 중앙 일/주/월 캘린더 뷰
  - 우측 검색, AI 일정 입력, 직접 입력 작업 공간
  - 중요 일정 알림과 우선순위 추천
