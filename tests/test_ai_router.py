from personal_assistant.ai_router import route_ai_command


def test_route_schedule_query() -> None:
    route = route_ai_command("이번 주 면접 일정 알려줘")

    assert route.intent == "query"
    assert route.menu == "상세 정보"


def test_route_event_creation() -> None:
    route = route_ai_command("내일 오전 10시에 회의 등록해줘")

    assert route.intent == "create_event"


def test_route_google_sync() -> None:
    route = route_ai_command("구글 캘린더 가져와")

    assert route.intent == "google_sync"
    assert route.menu == "Google 연동"


def test_route_site_collection() -> None:
    route = route_ai_command("관심 사이트 공고 수집해줘")

    assert route.intent == "collect_sites"
    assert route.menu == "관심 사이트"


def test_route_site_collection_and_calendar_registration() -> None:
    route = route_ai_command("외부 공고를 수집해서 캘린더 일정으로 등록해줘")

    assert route.intent == "collect_and_register_sites"
    assert route.menu == "관심 사이트"


def test_route_analysis_menus() -> None:
    assert route_ai_command("우선순위 추천해줘").intent == "priority"
    assert route_ai_command("리스크 분석해줘").intent == "risk"
    assert route_ai_command("실행 계획 만들어줘").intent == "execution_plan"
    assert route_ai_command("브리핑 생성해줘").intent == "briefing"
