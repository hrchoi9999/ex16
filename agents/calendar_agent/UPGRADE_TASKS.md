# Calendar Agent Upgrade Tasks

## 담당

일정 도메인, SQLite 저장소, Google Calendar 동기화 관련 업그레이드.

## 준비 작업

- 신규 기능이 일정 schema에 미치는 영향 분석
- 반복 일정, 외부 일정 후보, sync status, source metadata 확장 검토
- 일/주/월 view query 영향 검토

## QA 기준

- 일정 등록/조회/변경 기본 흐름이 유지되어야 한다.
- 외부 연동 일정과 로컬 일정의 중복 처리 기준이 명확해야 한다.
- KST 기준 날짜/시간 해석이 일관되어야 한다.
