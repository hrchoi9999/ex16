# QA Agent 역할과 적용 원칙

## 역할

`qa_agent`는 기능 테스트, 회귀 검증, 로컬 배포 확인을 담당한다.

## 업무 범위

- SQLite 일정 CRUD 테스트
- 일/주/월 view 이동과 화면 렌더링 확인
- AI 입력, 직접 등록, Google Calendar 가져오기 흐름 검증
- 외부 adapter mock 테스트
- `http://localhost:8501` 로컬 배포 확인

## 적용 원칙

- 기능 변경에는 가능한 한 pytest를 함께 실행한다.
- 외부 API 테스트는 credential 없이도 mock으로 검증 가능해야 한다.
- 화면 변경은 브라우저에서 실제 렌더링을 확인한다.
- 배포 확인 결과와 실패 원인은 총괄 이력에 남긴다.
