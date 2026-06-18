# Calendar Agent Phase 1 Tasks

## 목표

일정 저장과 조회/변경 기능의 신뢰성을 높이고 Google Calendar 확장 지점을 관리한다.

## 작업

- SQLite 이벤트 스키마와 CRUD 동작을 점검한다.
- 일정 시간 저장 형식과 표시 형식을 일관되게 유지한다.
- Google Calendar API 인증이 없을 때 로컬 저장이 계속 동작하는지 확인한다.
- 후속 작업에서 Google Calendar 이벤트 변경/삭제 동기화 방안을 설계한다.

## 완료 기준

- 일정 등록, 조회, 변경, 삭제 테스트가 통과한다.
- 외부 API 설정이 없어도 앱이 정상 동작한다.

