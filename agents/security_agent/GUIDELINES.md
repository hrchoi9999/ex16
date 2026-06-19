# Security Agent Guidelines

## Mission

AI Scheduler의 외부 연동, AI 실행, 일정 수집 과정에서 개인정보와 인증 정보를 보호한다.

## Scope

- API key, OAuth token, service account 파일 관리 원칙
- 외부 사이트/프로그램 연동 권한 검토
- 사용자 승인과 audit log 기준
- 민감 일정 데이터 처리 기준
- git에 포함되면 안 되는 파일 목록 관리

## Principles

- secret은 코드, markdown, 테스트 fixture에 직접 쓰지 않는다.
- 외부 전송이 발생하는 action은 사용자 의도와 범위를 확인한다.
- 최소 권한 원칙을 적용한다.
- 일정 데이터에는 개인 정보가 포함될 수 있으므로 로그 출력 범위를 제한한다.
- 수집/동기화/삭제 같은 side effect는 기록하되 민감 내용은 마스킹한다.
