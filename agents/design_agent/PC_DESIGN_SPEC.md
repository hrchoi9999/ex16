# PC Design Spec

## Reference

- Stitch zip: `C:\Users\kosa\Downloads\stitch_ai_workspace_calendar.zip`
- Extracted reference: `stitch_reference/stitch_ai_workspace_calendar/`
- Primary PC reference: `stitch_reference/stitch_ai_workspace_calendar/pc/code.html`
- Visual reference: `stitch_reference/stitch_ai_workspace_calendar/pc/screen.png`
- Design notes: `stitch_reference/stitch_ai_workspace_calendar/handover.md`

## Product Direction

PC용 개인 일정 관리 AI 에이전트 화면을 먼저 구현한다. 모바일 화면은 이후 별도 프로젝트 범위로 분리한다.

## Required Title And Font

- 화면 제목은 `AI Scheduler`로 표시한다.
- 기본 글꼴은 한글 가독성을 우선한다.
- CSS font stack은 `Pretendard`, `Noto Sans KR`, `Apple SD Gothic Neo`, `Malgun Gothic`, `Inter`, `Roboto`, `Arial`, `sans-serif` 순서로 둔다.

## Layout

- Top command bar: 제품명, 전역 검색, 날짜 표시, 알림, 프로필.
- Left panel: 워크스페이스 프로필, Week/Day/Month 메뉴, 연동 상태, 작은 월간 캘린더, 오늘 일정 요약.
- Center panel: 주간 캘린더 그리드와 시간대별 일정 블록.
- Right panel: AI Smart Assistant, 우선순위 추천 작업, 생산성 지표.
- Bottom interaction panel: AI 일정 입력, 직접 등록, 일정 조회 및 변경.

## Visual Style

- Stitch PC 시안의 밝은 생산성 대시보드 톤을 따른다.
- 배경은 `#f8f9ff`, 주요 표면은 흰색, 좌측 패널은 옅은 블루 컨테이너로 구성한다.
- 주요 액션과 활성 상태는 `#004ac6` 및 `#2563eb`를 사용한다.
- 기업형 B2B 일정 관리 도구답게 정보 밀도를 유지하고 장식적 요소는 줄인다.

## Agent Guidelines

- design_agent는 Stitch reference와 본 문서를 기준으로 UI 토큰, 레이아웃, 반응형 기준을 관리한다.
- lead_dev_agent는 `app.py`와 Python/SQLite/Google Calendar 연동 구조를 유지하며 기능을 구현한다.
- qa_agent는 `pytest`, 앱 import, 로컬 브라우저 렌더링, 주요 문구 표시 여부를 검증한다.
