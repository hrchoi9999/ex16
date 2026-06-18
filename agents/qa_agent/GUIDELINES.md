# QA Agent Guidelines

## 책임

- 핵심 기능 테스트를 작성하고 실행한다.
- Streamlit 앱이 import 가능한지, SQLite 저장소가 동작하는지 확인한다.

## 원칙

- API 키가 없어도 통과하는 테스트를 기본으로 한다.
- 날짜 파싱처럼 깨지기 쉬운 기능은 예시 기반 테스트를 둔다.
- 작업 완료 전 `pytest`와 최소 import 검증을 수행한다.

