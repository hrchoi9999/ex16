from __future__ import annotations

import re
import ssl
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from html import unescape

from .config import settings
from .models import ExternalScheduleCandidate


REQUESTED_SITE_SOURCES = ("서울50플러스 일자리몽땅", "K-Startup")


@dataclass(frozen=True)
class CollectionResult:
    success: bool
    message: str
    candidates: list[ExternalScheduleCandidate]


@dataclass(frozen=True)
class SiteTarget:
    source: str
    category: str
    urls: tuple[str, ...]


def collect_interest_sites() -> CollectionResult:
    targets = (
        SiteTarget(
            "서울50플러스 일자리몽땅",
            "직업교육",
            (settings.seoul50plus_training_url, settings.seoul50plus_url),
        ),
        SiteTarget(
            "서울50플러스 일자리몽땅",
            "취업지원",
            (settings.seoul50plus_job_support_url, settings.seoul50plus_url),
        ),
        SiteTarget("K-Startup", "모집공고", (settings.kstartup_url,)),
    )

    candidates: list[ExternalScheduleCandidate] = []
    errors: list[str] = []

    for target in targets:
        try:
            parsed = _collect_target(target)
            candidates.extend(parsed)
            if not parsed:
                errors.append(f"{target.source} {target.category}: 모집중 후보 없음")
        except Exception as exc:
            errors.append(f"{target.source} {target.category}: {exc}")

    candidates = _dedupe(candidates)
    if not candidates:
        return CollectionResult(False, "요청한 관심 사이트에서 등록 가능한 모집중 후보를 찾지 못했습니다.", [])
    if errors:
        return CollectionResult(True, f"{len(candidates)}개 후보를 수집했습니다. 확인 필요: {' / '.join(errors)}", candidates)
    return CollectionResult(True, f"{len(candidates)}개 후보를 수집했습니다.", candidates)


def _collect_target(target: SiteTarget) -> list[ExternalScheduleCandidate]:
    for url in _unique(target.urls):
        html = _fetch(url)
        if target.source == "K-Startup":
            candidates = _extract_kstartup_candidates(html, target, url)
        else:
            candidates = _extract_seoul50plus_candidates(html, target, url)
        if candidates:
            return candidates
    return []


def _fetch(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 AI-Scheduler/1.0",
            "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
        },
    )
    try:
        response_context = urllib.request.urlopen(request, timeout=12)
    except Exception as exc:
        if "CERTIFICATE_VERIFY_FAILED" not in str(exc):
            raise
        response_context = urllib.request.urlopen(
            request,
            timeout=12,
            context=ssl._create_unverified_context(),  # Public notice pages only; no credentials are sent.
        )
    with response_context as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="ignore")


def _extract_seoul50plus_candidates(html: str, target: SiteTarget, base_url: str) -> list[ExternalScheduleCandidate]:
    anchors = re.findall(r"<a\b[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", html, flags=re.I | re.S)
    candidates: list[ExternalScheduleCandidate] = []

    for index, (href, raw_title) in enumerate(anchors):
        text = _clean(raw_title)
        period = _period_after_label(text, "모집기간")
        if not period:
            continue
        if target.category == "직업교육" and not _is_job_training_notice(text):
            continue
        if target.category == "취업지원" and not _is_job_support_notice(text):
            continue
        title = _seoul_title(text, target.category)
        if not title:
            continue
        candidates.append(
            ExternalScheduleCandidate(
                id=None,
                source=target.source,
                category=target.category,
                title=title[:180],
                recruitment_period=period,
                url=urllib.parse.urljoin(base_url, href) or f"{base_url}#seoul50plus-{index}",
                status="모집중",
                collected_at=datetime.now().isoformat(timespec="seconds"),
            )
        )
    return candidates[:20]


def _extract_kstartup_candidates(html: str, target: SiteTarget, base_url: str) -> list[ExternalScheduleCandidate]:
    lines = _html_lines(html)
    candidates: list[ExternalScheduleCandidate] = []
    seen_titles: set[str] = set()

    for index, line in enumerate(lines):
        if line.startswith("마감일자"):
            end_day = _first_date(line)
            title = _next_title(lines, index + 1)
            if title and title not in seen_titles:
                seen_titles.add(title)
                category = _previous_category(lines, index) or target.category
                candidates.append(
                    _candidate(target.source, category, title, f"마감일자 {end_day}", f"{base_url}#kstartup-{index}")
                )
        elif "시작일자" in line and "마감일자" in line:
            title = _title_before_registered_at(line)
            period = _period_from_start_end(line)
            if title and period and title not in seen_titles:
                seen_titles.add(title)
                category = _previous_category(lines, index) or target.category
                candidates.append(_candidate(target.source, category, title, period, f"{base_url}#kstartup-{index}"))

    return candidates[:30]


def _candidate(source: str, category: str, title: str, period: str, url: str) -> ExternalScheduleCandidate:
    return ExternalScheduleCandidate(
        id=None,
        source=source,
        category=category,
        title=title[:180],
        recruitment_period=period[:120],
        url=url,
        status="모집중",
        collected_at=datetime.now().isoformat(timespec="seconds"),
    )


def _clean(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value)
    value = unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def _html_lines(html: str) -> list[str]:
    text = re.sub(r"<br\s*/?>", "\n", html, flags=re.I)
    text = re.sub(r"</(p|li|div|tr|h\d)>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return [line for line in (_clean(line) for line in text.splitlines()) if line]


def _period_after_label(text: str, label: str) -> str:
    match = re.search(rf"{label}\s*:\s*(20\d{{2}}[.\-\/]\d{{1,2}}[.\-\/]\d{{1,2}}\s*[~\-]\s*20\d{{2}}[.\-\/]\d{{1,2}}[.\-\/]\d{{1,2}})", text)
    return match.group(1).strip() if match else ""


def _period_from_start_end(text: str) -> str:
    start = re.search(r"시작일자\s*(20\d{2}[.\-\/]\d{1,2}[.\-\/]\d{1,2})", text)
    end = re.search(r"마감일자\s*(20\d{2}[.\-\/]\d{1,2}[.\-\/]\d{1,2})", text)
    if start and end:
        return f"{start.group(1)} ~ {end.group(1)}"
    return ""


def _first_date(text: str) -> str:
    match = re.search(r"20\d{2}[.\-\/]\d{1,2}[.\-\/]\d{1,2}", text)
    return match.group(0) if match else "기간 확인 필요"


def _is_job_training_notice(text: str) -> bool:
    return "모집기간" in text and any(keyword in text for keyword in ("수강신청", "교육기간", "직무교육", "취업훈련", "AI 디지털 교육"))


def _is_job_support_notice(text: str) -> bool:
    labels = ("경력인재지원", "채용설명회", "민간채용공고", "외부채용공고")
    return "모집기간" in text and any(label in text for label in labels)


def _seoul_title(text: str, category: str) -> str:
    if category == "취업지원":
        text = re.sub(r"^(경력인재지원|채용설명회|민간채용공고|외부채용공고)\s*", "", text)
    title = re.split(r"\s+(활동비|정규직|계약직|기타|모집인원|모집기간|행사장소|무료)\s*:?", text, maxsplit=1)[0]
    return title.strip(" -·")


def _next_title(lines: list[str], start_index: int) -> str:
    for line in lines[start_index : start_index + 5]:
        title = line.replace("새로운게시글", "").strip()
        if title and not title.startswith("*") and "조회 " not in title:
            return title
    return ""


def _previous_category(lines: list[str], index: int) -> str:
    for line in reversed(lines[max(0, index - 4) : index]):
        if "D-" in line or "오늘마감" in line:
            return re.sub(r"\s*(D-\d+|오늘마감).*", "", line).strip(" *")
    return ""


def _title_before_registered_at(line: str) -> str:
    title = re.split(r"\s+등록일자\s+", line, maxsplit=1)[0]
    return title.replace("새로운게시글", "").strip()


def _dedupe(candidates: list[ExternalScheduleCandidate]) -> list[ExternalScheduleCandidate]:
    deduped: list[ExternalScheduleCandidate] = []
    seen: set[tuple[str, str]] = set()
    for candidate in candidates:
        key = (candidate.source, candidate.title)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(candidate)
    return deduped


def _unique(values: tuple[str, ...]) -> tuple[str, ...]:
    result: list[str] = []
    for value in values:
        if value and value not in result:
            result.append(value)
    return tuple(result)
