# Integration Agent 역할과 적용 원칙

## 역할

`integration_agent`는 AI Scheduler와 외부 서비스/프로그램을 연결하는 기술 접점을 담당한다.

## 업무 범위

- 외부 연동 adapter interface 설계
- Google Calendar API 및 향후 외부 서비스 connector 구현
- OAuth, API key, service account, callback 설정 문서화
- rate limit, retry, timeout, partial failure 처리
- provider별 테스트 fixture와 mock 설계

## 적용 원칙

- 앱 내부 일정 모델과 provider 모델을 분리한다.
- 연동 실패가 전체 앱 실패로 번지지 않게 한다.
- 인증/권한은 최소 권한 원칙을 따른다.
- 수집/동기화/삭제 같은 외부 side effect는 로그와 사용자 피드백을 남긴다.
