# Design Agent UI/UX Design Spec

## 적용할 디자인 프롬프트

Act as an expert UI/UX designer and frontend developer. Create a modern, professional, and minimalist UI design for a B2B business schedule and task management web application.

Target Audience: Corporate professionals, executives, and team managers.
Overall Style: Sleek, functional, data-centric dashboard, and clutter-free. Use a clean, modern sans-serif typography (e.g., Inter, Roboto, or Pretendard).

Color Palette:
- Theme: 'Corporate Trust & Productivity'
- Primary Color: Deep Navy Blue (#0F172A) or Slate.
- Background: Crisp White (#FFFFFF) for the main content and Light Gray (#F8F9FA) for sidebars/sections to ensure high readability.
- Accent/Semantic Colors: Subtle Muted Green for completed tasks, Soft Amber for pending, and Muted Red for urgent deadlines.

Layout & Core Components:
1. Sidebar Navigation: Collapsible vertical menu featuring minimalist icons for Dashboard, Calendar (Monthly/Weekly), Projects, Analytics, and Settings.
2. Top Header: Global search bar, date selector, notification bell, and user profile thumbnail.
3. Main Workspace (Dashboard View):
   - Interactive Calendar Module: Clean grid layout with color-coded, rounded-corner event blocks.
   - Upcoming Tasks Widget: A list view showing task names, priority tags, and deadlines.
   - Data Widget: A subtle data visualization element (e.g., a clean donut chart or progress bar) showing weekly task completion status.

Technical Requirements:
The design must be fully responsive. Please generate the code using modern HTML, CSS, and structural principles similar to Tailwind CSS, ensuring clean, modular, and maintainable code.

## 디자인 방향

- B2B 업무용 대시보드처럼 차분하고 기능 중심으로 설계한다.
- 장식보다 정보 밀도, 스캔 가능성, 반복 사용 편의성을 우선한다.
- Streamlit UI에서도 사이드바, 상단 작업 영역, 대시보드 카드가 명확히 구분되도록 CSS를 적용한다.
- 색상은 네이비, 흰색, 밝은 회색을 기반으로 하고 상태 색상만 제한적으로 사용한다.

## 디자인 토큰

| Token | Value | Purpose |
| --- | --- | --- |
| `--color-primary` | `#0F172A` | 헤더, 주요 텍스트, 핵심 버튼 |
| `--color-bg` | `#FFFFFF` | 메인 콘텐츠 배경 |
| `--color-surface` | `#F8F9FA` | 사이드바와 보조 섹션 |
| `--color-complete` | `#2F855A` | 완료/안정 상태 |
| `--color-pending` | `#B7791F` | 대기/주의 상태 |
| `--color-urgent` | `#C2410C` | 긴급/마감 임박 |
| `--font-sans` | `Pretendard, Inter, Roboto, sans-serif` | 전체 UI |

## 핵심 컴포넌트

- Sidebar Navigation: Dashboard, Calendar, Projects, Analytics, Settings
- Top Header: 글로벌 검색, 날짜 선택, 알림, 프로필
- Calendar Module: 월간/주간 그리드, 상태별 일정 블록
- Upcoming Tasks Widget: 일정명, 우선순위 태그, 마감 시간
- Data Widget: 주간 완료율 프로그레스 바 또는 도넛 차트

## 1차 디자인 작업 지시

- 현재 Streamlit 화면을 B2B 대시보드 톤으로 개선한다.
- 사이드바에는 앱 이름과 주요 메뉴를 배치한다.
- 상단에는 검색어 입력, 날짜 선택, 알림 상태, 사용자 프로필 표시 영역을 둔다.
- 메인 대시보드는 일정 등록, 일정 조회/변경, 중요 알림, 우선순위 추천이 균형 있게 보이도록 재배치한다.
- CSS는 `app.py` 안의 작은 스타일 블록에서 시작하고, 필요 시 후속 작업에서 별도 파일로 분리한다.

