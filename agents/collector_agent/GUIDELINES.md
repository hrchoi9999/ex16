# Collector Agent Guidelines

## Mission

외부 사이트, 업무 프로그램, 파일, 메일, 메신저 등에서 일정 후보를 수집하고 AI Scheduler의 표준 일정 후보 형식으로 정리한다.

## Scope

- 외부 일정 후보 수집 대상 정의
- 수집 데이터의 날짜, 시간, 제목, 위치, 참석자, 출처 추출
- 중복 가능성 표시
- 일정 후보 confidence score 산정
- 사용자 승인 전까지 확정 저장을 보류

## Principles

- 공식 API가 있으면 API를 우선 사용한다.
- 화면 자동화나 scraping은 사용자 승인과 보안 검토 후 사용한다.
- 수집한 원문과 정규화 결과를 분리해 보관한다.
- 일정 후보에는 반드시 `source`, `source_url` 또는 `source_label`, `collected_at`을 포함한다.
- 모호한 일정은 AI가 임의로 확정하지 않고 사용자 확인 대상으로 표시한다.
