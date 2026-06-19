# QA Agent Upgrade Tasks

## 담당

업그레이드 산출물의 품질관리, 테스트, 회귀 검증, 로컬 배포 확인.

## 준비 작업

- 기능별 acceptance criteria 수집
- 테스트 범위 정의: unit, integration mock, UI smoke, deployment
- 회귀 테스트 체크리스트 관리
- 배포 확인 결과 기록

## QA Gate

| Gate | 확인 항목 | 통과 기준 |
| --- | --- | --- |
| 문서 | 기능 분석/agent 배정/완료 기준 존재 | 관련 MD 업데이트 |
| 코드 | import 및 lint 수준 오류 없음 | 앱 import 성공 |
| 테스트 | pytest 또는 기능별 검증 | 실패 없음 |
| UI | 주요 화면 렌더링 | `http://localhost:8501`에서 확인 |
| 데이터 | SQLite CRUD 및 schema 호환 | 기존 데이터 손상 없음 |
| 보안 | secret 미포함, 권한 검토 | git diff에 secret 없음 |
| 배포 | 로컬 실행 가능 | Streamlit URL 접근 가능 |

## 회귀 체크리스트

- 일정 직접 등록
- 일정 조회
- 일정 변경
- 일/주/월 view 이동
- AI 일정 입력 영역 표시
- Google Calendar 가져오기 버튼 동작
- 중요한 일정/우선순위 영역 표시
- 외부 수집 후보가 확정 일정과 구분됨
