# Calendar Agent Phase 1 Tasks

## 목표

일정 저장, 조회, 변경, 삭제 기능의 안정성을 높이고 Google Calendar 연동 확장 지점을 관리한다.

## 완료된 작업

- SQLite 이벤트 스키마와 CRUD 동작을 검증한다.
- `google_event_id` 기준 upsert를 추가해 Google Calendar에서 가져온 일정이 중복 저장되지 않도록 한다.
- Google Calendar API 등록, 조회, 변경, 삭제 클라이언트 메서드를 제공한다.
- 일/주/월 화면 범위에 맞춰 Google Calendar 일정을 가져오고 SQLite에 반영하는 흐름을 앱에 연결한다.
- Google API 설정이 없는 경우 로컬 기능이 계속 동작하고 사용자에게 설정 안내를 표시한다.

## 후속 작업

- 실제 서비스 계정 파일과 공유 캘린더 권한으로 end-to-end 동기화를 검증한다.
- Google Calendar 반복 일정, 참석자, 알림 필드 동기화 범위를 확장한다.
- 로컬 삭제와 Google 삭제의 실패 보상 정책을 정한다.

## 완료 기준

- 일정 등록, 조회, 변경, 삭제 테스트가 통과한다.
- Google Calendar import가 `google_event_id` 기준으로 중복 없이 갱신된다.
- API 설정이 없어도 앱이 오류 없이 로컬 일정 관리 기능을 제공한다.
