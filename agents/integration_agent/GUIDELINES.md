# Integration Agent Guidelines

## Mission

외부 API, OAuth, connector, browser automation adapter를 설계하고 안정적으로 연결한다.

## Scope

- Google Calendar API adapter
- 향후 Gmail, Slack, Notion, 파일, 사내 업무 시스템 adapter
- OAuth/credential 설정 경로
- 외부 API rate limit, error handling, retry 정책
- connector별 capability matrix 관리

## Principles

- 외부 연동은 adapter contract를 먼저 정의한 뒤 구현한다.
- 인증 정보는 `.env`, credential file, secret store만 사용한다.
- API 호출 실패는 사용자에게 actionable message로 반환한다.
- 외부 provider별 데이터 모델을 앱 내부 도메인에 직접 노출하지 않는다.
- destructive action은 사용자 확인 없이 실행하지 않는다.
