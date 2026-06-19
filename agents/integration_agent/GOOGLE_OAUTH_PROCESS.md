# Google Calendar OAuth 연동 프로세스

## 담당 Agent

`integration_agent`가 Google OAuth와 Google Calendar API 연동의 주 담당자다.

협업 범위:

- `calendar_agent`: Calendar API 가져오기, 등록, 변경, 삭제 동기화
- `security_agent`: OAuth client secret, token file, scope, redirect URI 보안 검토
- `design_agent`: 관리자 설정 안내와 사용자 로그인 UX
- `qa_agent`: 최초 실행, 회원가입, 회원 로그인, 토큰 만료/재동의 검증

## 핵심 원칙

- Gmail 계정으로 Google 로그인해서 개인 Google Calendar 일정을 가져오는 것은 가능하다.
- 일반 사용자는 Client ID, Client Secret, token file을 입력하지 않는다.
- 관리자는 Google Cloud OAuth 클라이언트를 한 번 준비하고 서버 환경에 설정한다.
- 앱은 사용자에게 Google 로그인 URL을 제공하고, Google OAuth callback code를 받아 토큰으로 교환한다.
- redirect URI는 앱 설정값과 Google Cloud Console의 Authorized redirect URI가 정확히 일치해야 한다.
- OAuth token file은 외부 저장소에 커밋하지 않는다.

## 관리자 준비 사항

관리자는 앱 최초 배포 전에 아래 항목을 준비한다.

1. Google Cloud Console에서 프로젝트를 생성하거나 선택한다.
2. API Library에서 Google Calendar API를 활성화한다.
3. OAuth consent screen을 구성한다.
4. 테스트 단계라면 테스트 사용자에 사용할 Gmail 계정을 등록한다.
5. Credentials에서 OAuth Client ID를 생성한다.
6. Application type은 Web application으로 선택한다.
7. Authorized redirect URI에 로컬 개발 기준 `http://localhost:8501/`를 등록한다.
8. 발급된 Client ID와 Client Secret을 `.env`에 저장한다.
9. 앱을 재시작한다.

`.env` 예시:

```dotenv
GOOGLE_CALENDAR_ID=primary
GOOGLE_OAUTH_CLIENT_ID=발급받은_CLIENT_ID
GOOGLE_OAUTH_CLIENT_SECRET=발급받은_CLIENT_SECRET
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8501/
GOOGLE_OAUTH_TOKEN_FILE=data/google_token.json
```

## 일반 사용자 처리 사항

일반 사용자는 아래 행동만 수행한다.

1. 앱에서 `Google 로그인 열기`를 클릭한다.
2. Google 로그인 화면에서 Gmail 계정으로 로그인한다.
3. Google Calendar 권한 요청을 확인하고 동의한다.
4. 앱으로 돌아온 뒤 가져온 일정을 확인한다.

사용자는 OAuth Client ID, Client Secret, token file을 직접 입력하지 않는다.

## 프로세스 1: 앱 최초 실행

목표: 운영 설정 상태를 판별하고 다음 행동을 명확히 안내한다.

개발 지시:

- `settings.google_oauth_enabled`가 false이면 Google 로그인 버튼은 설정 필요 상태를 안내한다.
- 우측 Google 연동 패널에 관리자 설정 순서와 `.env` 예시를 표시한다.
- `GOOGLE_OAUTH_REDIRECT_URI`와 앱 접속 URL이 불일치할 수 있음을 안내한다.
- OAuth token file이 없더라도 앱의 로컬 일정 기능은 계속 동작해야 한다.

QA 기준:

- OAuth 설정이 없을 때도 앱은 중단되지 않는다.
- 관리자가 해야 할 작업과 사용자가 해야 할 작업이 화면에서 구분된다.

## 프로세스 2: 회원 가입

목표: 사용자가 Gmail 계정으로 Calendar 권한을 연결한다.

개발 지시:

- 사용자가 `Google 로그인 열기`를 누르면 OAuth authorization URL을 생성한다.
- 생성된 URL은 `Google 로그인 화면 열기` 링크로 제공한다.
- OAuth 요청에는 Calendar scope, redirect URI, offline access, state 값을 포함한다.
- Google callback의 `code`를 받아 access token과 refresh token으로 교환한다.
- 토큰 저장 후 앱 사용자 레코드를 등록한다.
- 가입 완료 직후 현재 보기 범위의 Google Calendar 일정을 가져온다.

QA 기준:

- 잘못된 redirect URI일 때 Google의 `redirect_uri_mismatch` 오류를 관리자 조치 항목으로 안내한다.
- 사용자가 동의를 취소하면 앱은 취소 메시지를 표시하고 로컬 기능을 유지한다.

## 프로세스 3: 회원 로그인

목표: 기존 토큰이 있으면 재동의 없이 Calendar API를 사용한다.

개발 지시:

- `GOOGLE_OAUTH_TOKEN_FILE`이 존재하고 유효하면 API 호출에 재사용한다.
- access token이 만료되고 refresh token이 있으면 자동 갱신한다.
- refresh 실패 시 다시 Google 로그인 링크를 생성하도록 안내한다.
- 로그인 후 현재 보기 범위 가져오기, 일정 등록/변경/삭제 동기화를 수행한다.

QA 기준:

- 기존 토큰이 유효하면 로그인 링크 없이 일정 가져오기가 가능하다.
- 토큰 파일 삭제 후에는 다시 가입/연동 프로세스를 안내한다.

## 참고 문서

- Google OAuth 2.0 Web Server Applications: https://developers.google.com/identity/protocols/oauth2/web-server
- Google Calendar API Python Quickstart: https://developers.google.com/calendar/api/quickstart/python
