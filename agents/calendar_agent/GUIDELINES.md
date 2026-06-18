# Calendar Agent Guidelines

## 책임

- SQLite 스키마와 일정 CRUD 로직을 관리한다.
- Google Calendar API 어댑터를 분리해 외부 인증 실패가 앱 전체 실패로 번지지 않게 한다.

## 원칙

- 일정 시간은 ISO 문자열로 저장하고 화면에서 한국 시간으로 표시한다.
- 변경 작업은 기존 일정 ID를 기준으로 수행한다.
- Google Calendar 연동은 선택 기능이며, 로컬 저장을 기본 진실 소스로 둔다.

