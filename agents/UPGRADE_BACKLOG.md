# Upgrade Backlog

## 상태

신규 기능 목록 접수 완료. 1차 업그레이드 구현 진행 중.

## 기능 접수 후 작성 기준

각 기능은 아래 형식으로 등록한다.

```text
ID:
기능명:
사용자 가치:
대표 시나리오:
주 담당 agent:
협업 agent:
필요 화면:
필요 데이터:
외부 연동:
AI 연동:
보안/권한:
완료 기준:
QA 기준:
상태:
```

## 예비 Epic

| Epic | 설명 | 예상 담당 |
| --- | --- | --- |
| 일정 관리 고도화 | 일정 등록/조회/변경/삭제, 반복 일정, 세부 필터 | calendar_agent, design_agent |
| 외부 일정 수집 | Google Calendar 외 사이트/프로그램에서 일정 후보 수집 | collector_agent, integration_agent, security_agent |
| AI 일정 비서 | 자연어로 일정 확인, 등록, 변경, 수집 실행 | ai_agent, calendar_agent |
| 알림/우선순위 | 중요한 일정 알림, 우선순위 추천, 생산성 지표 | notification_agent, priority_agent |
| 품질/배포 | 테스트, 로컬 배포, 회귀 검증, 산출물 검수 | qa_agent, lead_dev_agent |

## 접수된 기능

| ID | 기능명 | 사용자 가치 | 주 담당 agent | 협업 agent | 상태 |
| --- | --- | --- | --- | --- | --- |
| UPG-001 | 캘린더 하단 기능 정리 | 캘린더 하단은 선택 상세와 AI 채팅 중심으로 단순화 | design_agent | lead_dev_agent, qa_agent | 진행 |
| UPG-002 | 구글 계정 사용자 등록/연동 | 구글 계정 등록 후 Google Calendar 일정을 가져옴 | integration_agent | calendar_agent, security_agent, design_agent | 진행 |
| UPG-003 | 일정 편집 기능 강화 | 일/주/월에서 일정 입력/수정/삭제 흐름 제공 | calendar_agent | design_agent, lead_dev_agent, qa_agent | 진행 |
| UPG-004 | Google Calendar 자동 동기화 | 등록/변경/삭제가 Google Calendar와 동기화 | calendar_agent | integration_agent, security_agent | 진행 |
| UPG-005 | 관심 사이트 일정 크롤링 | 서울50플러스/K-Startup 모집중 공고 후보 수집 | collector_agent | integration_agent, security_agent, calendar_agent | 진행 |
| UPG-006 | Gemini AI 일정 채팅 | 일정 질의 결과를 우측에 표시하고 캘린더 일정 강조 | ai_agent | calendar_agent, design_agent | 진행 |
| UPG-007 | 캘린더 월 기본/월 이동 UI | 기본 월 view 및 월 이동 꺾쇠 제공 | design_agent | calendar_agent | 진행 |
