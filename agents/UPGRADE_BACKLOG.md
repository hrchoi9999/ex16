# Upgrade Backlog

## 상태

구체적인 신규 기능 목록 입력 대기 중.

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
