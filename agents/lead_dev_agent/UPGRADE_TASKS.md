# Lead Dev Agent Upgrade Tasks

## 담당

업그레이드 구현 구조, 통합 순서, 배포 가능 상태 관리.

## 준비 작업

- 신규 기능을 모듈 단위로 배치
- DB 변경이 필요한 기능은 calendar_agent와 schema 영향 검토
- 외부 연동은 integration adapter 경계를 먼저 정의
- commit/push 단위를 기능별로 관리

## QA 기준

- `python -m pytest` 또는 기능별 검증이 통과해야 한다.
- `streamlit run app.py`로 로컬 배포가 가능해야 한다.
- 변경 기능이 기존 일정 CRUD와 충돌하지 않아야 한다.
