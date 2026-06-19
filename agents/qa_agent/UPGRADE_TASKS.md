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
- 일정 삭제
- 일/주/월 view 이동
- 월 기본 화면과 월 이동 꺾쇠
- AI 일정 입력 영역 표시
- AI 채팅 결과와 일정 강조
- Google Calendar 가져오기 버튼 동작
- Google 계정 등록 UI와 자동 가져오기 안내
- 관심 사이트 후보 수집 목록 표시
- 중요한 일정/우선순위 영역 표시
- 외부 수집 후보가 확정 일정과 구분됨

## 2026-06-19 병렬 수정 작업

- CSS 변경 후 월 캘린더의 폰트가 과하게 굵지 않은지 브라우저에서 확인한다.
- AI 채팅은 API 키 미설정 상태에서도 로컬 검색 답변이 나오는지 확인한다.
- 관심 사이트 수집 결과가 서울50플러스/K-Startup 지정 소스만 포함하는지 테스트한다.
- Google Calendar 연동은 Codex 플러그인 인증과 로컬 앱 OAuth/API 인증이 분리된다는 설명을 사용자에게 남긴다.
