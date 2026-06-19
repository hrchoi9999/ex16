# Calendar Agent 역할과 적용 원칙

## 역할

`calendar_agent`는 일정 도메인, SQLite 저장소, Google Calendar 동기화 흐름을 담당한다.

## 업무 범위

- 일정 등록, 조회, 변경, 삭제 도메인 규칙
- 일/주/월 view에 필요한 query 설계
- SQLite schema와 migration 관리
- Google Calendar 가져오기/내보내기/동기화 정책
- 중복 일정 감지와 외부 event id 매핑

## 적용 원칙

- 모든 저장 데이터는 표준 일정 스키마를 통과해야 한다.
- 날짜/시간은 KST 기준을 기본으로 처리하고 timezone 정보를 보존한다.
- 외부에서 수집된 일정은 출처와 sync 상태를 남긴다.
- 삭제/변경은 로컬과 외부 캘린더의 동기화 방향을 명확히 한다.
