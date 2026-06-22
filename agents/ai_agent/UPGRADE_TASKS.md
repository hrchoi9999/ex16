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

## 2026-06-19 병렬 수정 작업

- Gemini API 키가 없거나 호출이 실패해도 로컬 일정 검색 fallback으로 답변한다.
- "오늘 일정", "이번 주 일정", "이번 달 일정" 같은 일반 질문은 등록된 일정 목록에서 요약 답변을 생성한다.
- 답변과 함께 매칭된 event id를 반환해 캘린더에서 해당 일정 강조 효과를 적용할 수 있게 한다.

## 2026-06-22 BabyAGI 우선순위 1 구현 작업

- 실행 분해형 AI 플래너를 `실행 계획` 작업 메뉴로 추가한다.
- 일정/공고를 `오늘 할 일`, `이번주 준비`, `마감전 체크` 항목으로 분해한다.
- Gemini API가 없을 때도 규칙 기반 체크리스트 생성 fallback을 제공한다.
- 생성된 항목의 완료 상태와 캘린더 반영 상태는 SQLite 기준으로 관리한다.
