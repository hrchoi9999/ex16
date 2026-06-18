# Lead Dev Agent Phase 1 Tasks

## 목표

기능 Agent의 산출물이 안정적으로 통합될 수 있도록 코드 구조와 검증 기준을 관리한다.

## 작업

- `personal_assistant/` 모듈 책임 경계를 유지한다.
- Streamlit UI와 도메인 로직이 과하게 섞이지 않도록 관리한다.
- Google Calendar와 LLM 연동은 선택 기능으로 유지한다.
- 커밋 전 변경 파일, 테스트 결과, 실행 검증을 확인한다.

## 완료 기준

- `pytest`가 통과한다.
- `app.py`가 import 가능하다.
- 새 파일은 목적이 명확한 위치에 있다.
- 작업 단위가 끝난 뒤 원격 저장소에 push된다.

