# Integration Agent Upgrade Tasks

## 담당

외부 API, OAuth, connector, adapter 구현 준비.

## 준비 작업

- provider별 adapter contract 정의
- credential 설정 방식 문서화
- timeout/retry/rate limit 정책 정의
- mock 테스트가 가능한 구조 설계
- Google OAuth client secret/token 설정 확장
- Google 계정 등록 시 Calendar 자동 가져오기 흐름 연결

## QA 기준

- 인증 정보가 git에 포함되지 않아야 한다.
- 외부 API 실패가 전체 앱 오류로 번지지 않아야 한다.
- 읽기/쓰기/삭제 권한이 분리되어야 한다.
