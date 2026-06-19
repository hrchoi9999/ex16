# Security Agent Upgrade Tasks

## 담당

외부 연동, AI 실행, 일정 수집 과정의 개인정보와 권한 관리.

## 준비 작업

- secret 관리 기준 재확인
- 외부 사이트/프로그램별 권한 범위 검토
- 사용자 승인 필요한 action 목록 정의
- 로그 마스킹 기준 정리

## QA 기준

- API key, OAuth token, credential 파일이 git에 포함되지 않아야 한다.
- 외부 전송/삭제/변경 action은 사용자 의도와 범위가 명확해야 한다.
- 민감 일정 데이터가 로그에 과도하게 남지 않아야 한다.
