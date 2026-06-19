# Calendar Agent Upgrade Tasks

## 담당

일정 도메인, SQLite 저장소, Google Calendar 동기화 관련 업그레이드.

## 준비 작업

- 일정 schema에 source/source_url/sync metadata 확장
- 일 view 시간 단위 등록/수정/삭제 구현
- 주/월 날짜 선택 후 해당 날짜 편집 흐름 구현
- Google Calendar 등록/변경/삭제 동기화 유지
- 외부 수집 후보를 선택 시 일정으로 등록하는 흐름 구현

## QA 기준

- 일정 등록/조회/변경 기본 흐름이 유지되어야 한다.
- 외부 연동 일정과 로컬 일정의 중복 처리 기준이 명확해야 한다.
- KST 기준 날짜/시간 해석이 일관되어야 한다.
