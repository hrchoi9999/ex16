# AI Agent 역할과 적용 원칙

## 역할

`ai_agent`는 사용자의 자연어 명령을 일정 관리 action으로 바꾸고, Gemini API 또는 OpenAI Platform 연동을 담당한다.

## 업무 범위

- 일정 등록/조회/변경/수집 명령 intent parsing
- 날짜/시간/반복/참석자/중요도 추출
- AI action planning 및 실행 결과 설명
- 외부 수집 요청을 `collector_agent`와 `integration_agent`에 위임
- LLM provider 교체 가능한 interface 관리

## 적용 원칙

- AI 응답은 저장 전 스키마 검증을 통과해야 한다.
- 모호한 날짜/시간은 KST 기준으로 해석하고, 위험하면 사용자 확인을 요청한다.
- AI가 실행할 action은 사용자에게 짧고 명확하게 설명한다.
- 추천과 자동 분류에는 근거를 함께 표시한다.
