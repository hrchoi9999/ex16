# Local Deployment

## Current Local URL

- Streamlit app: http://localhost:8501
- Verified at: 2026-06-18 16:29:18 +09:00

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
  - 라이트 테마 기반 B2B 대시보드
  - 상단 글로벌 검색, 날짜 선택, 알림, 프로필
  - 좌측 축소형 월간 캘린더와 메뉴
  - 중앙 일/주/월 캘린더 뷰
  - 우측 검색, AI 일정 입력, 직접 입력 작업 공간
  - 주간 완료율, 중요 일정 알림, 우선순위 추천
  - Chrome Google Calendar에서 가져온 2026년 6월 일정
