from __future__ import annotations

from personal_assistant.site_collector import (
    SiteTarget,
    _extract_kstartup_candidates,
    _extract_seoul50plus_candidates,
)


def test_extract_seoul50plus_training_candidate() -> None:
    html = """
    <a href="/lecture/detail.do">
      관악센터 청소연구소 플랫폼 직무교육 무료 모집인원 : 20명
      모집기간 : 2026-06-19 ~ 2026-07-14 교육기간 : 2026-07-15 ~ 2026-07-15 수강신청 (D-25)
    </a>
    """
    target = SiteTarget("서울50플러스 일자리몽땅", "직업교육", ("https://www.50plus.or.kr/",))

    candidates = _extract_seoul50plus_candidates(html, target, "https://www.50plus.or.kr/")

    assert len(candidates) == 1
    assert candidates[0].source == "서울50플러스 일자리몽땅"
    assert candidates[0].category == "직업교육"
    assert candidates[0].status == "모집중"
    assert "2026-06-19" in candidates[0].recruitment_period


def test_extract_seoul50plus_job_support_candidate() -> None:
    html = """
    <a href="/job/detail.do">
      경력인재지원 온어스특허법률사무소 중장년 경력 인재 지원 참여자 모집
      활동비 : 시급 12,121 원 모집인원 : 1명 모집기간 : 2026-06-19-2026-07-02 신청 · 접수하기(D-13)
    </a>
    """
    target = SiteTarget("서울50플러스 일자리몽땅", "취업지원", ("https://www.50plus.or.kr/",))

    candidates = _extract_seoul50plus_candidates(html, target, "https://www.50plus.or.kr/")

    assert len(candidates) == 1
    assert candidates[0].category == "취업지원"
    assert candidates[0].title.startswith("온어스특허법률사무소")


def test_extract_kstartup_ongoing_candidate() -> None:
    html = """
    <div>행사ㆍ네트워크 D-21</div>
    <div>마감일자 2026-07-10</div>
    <div>2026년 민관협력 오픈이노베이션 창업기업 모집공고 새로운게시글</div>
    """
    target = SiteTarget("K-Startup", "모집공고", ("https://www.k-startup.go.kr/web/contents/bizpbanc-ongoing.do",))

    candidates = _extract_kstartup_candidates(html, target, target.urls[0])

    assert len(candidates) == 1
    assert candidates[0].source == "K-Startup"
    assert candidates[0].category == "행사ㆍ네트워크"
    assert candidates[0].recruitment_period == "마감일자 2026-07-10"
