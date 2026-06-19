# AI Agent Upgrade Tasks

## 담당

자연어 명령 해석, AI 일정 확인/등록/변경/수집 실행.

## 준비 작업

- intent 종류 정의: create, read, update, collect, summarize, recommend
- LLM 응답 schema 검증 기준 작성
- 모호한 날짜/시간 확인 질문 정책 정리
- Gemini/OpenAI provider interface 유지
- Gemini API key 기반 우측 AI 채팅 구현
- 일정 질의 결과와 matching event id 반환
- 캘린더의 해당 일정 깜빡임 강조 상태 연동

## QA 기준

- AI 결과가 바로 DB에 저장되기 전 schema 검증을 통과해야 한다.
- 모호한 명령은 무리하게 실행하지 않아야 한다.
- 실행 결과는 사용자가 이해할 수 있는 한국어로 제공해야 한다.
