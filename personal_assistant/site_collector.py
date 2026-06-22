from __future__ import annotations

import re
import ssl
import urllib.parse
import urllib.request
import json
from dataclasses import dataclass
from datetime import date, datetime
from html import unescape

from .config import settings
from .models import ExternalScheduleCandidate


REQUESTED_SITE_SOURCES = ("서울50플러스 일자리몽땅", "서울경제진흥원", "서울창조경제혁신센터", "K-Startup")


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
    extractor: str = "seoul50plus"
    status_keywords: tuple[str, ...] = ()


def collect_interest_sites() -> CollectionResult:
    targets = (
        SiteTarget(
            "서울50플러스 일자리몽땅",
            "직업교육/취업훈련",
            (settings.seoul50plus_vocational_training_url,),
            extractor="seoul50plus_app",
            status_keywords=("IN17003",),
        ),
        SiteTarget(
            "서울50플러스 일자리몽땅",
            "직업교육/AI디지털교육",
            (settings.seoul50plus_ai_digital_list_url,),
            extractor="seoul50plus_education",
            status_keywords=("수강신청", "대기신청"),
        ),
        SiteTarget(
            "서울50플러스 일자리몽땅",
            "취업지원/민간채용공고",
            (settings.seoul50plus_private_job_url,),
            extractor="seoul50plus_app",
            status_keywords=("IN17003",),
        ),
        SiteTarget(
            "서울경제진흥원",
            "모집공고",
            (settings.sba_notice_url,),
            extractor="sba",
            status_keywords=("모집중",),
        ),
        SiteTarget(
            "서울창조경제혁신센터",
            "알림마당/사업공고",
            (settings.seoul_ccei_notice_url, settings.seoul_ccei_oi_url),
            extractor="seoul_ccei",
        ),
        SiteTarget("K-Startup", "모집공고", (settings.kstartup_url,), extractor="kstartup", status_keywords=("모집중",)),
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
        if target.extractor == "seoul50plus_app":
            candidates = _extract_seoul50plus_app_candidates(target, url)
            if candidates:
                return candidates
            continue
        html = _fetch(url)
        if target.extractor == "kstartup":
            candidates = _extract_kstartup_candidates(html, target, url)
        elif target.extractor == "sba":
            candidates = _extract_sba_candidates(html, target, url)
        elif target.extractor == "seoul_ccei":
            candidates = _extract_seoul_ccei_candidates(html, target, url)
        elif target.extractor == "seoul50plus_education":
            candidates = _extract_seoul50plus_education_candidates(html, target, url)
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


def _fetch_json_post(url: str, params: dict[str, str], referer: str) -> dict:
    data = urllib.parse.urlencode(params).encode()
    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "User-Agent": "Mozilla/5.0 AI-Scheduler/1.0",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": referer,
        },
    )
    with urllib.request.urlopen(request, timeout=12) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return json.loads(response.read().decode(charset, errors="ignore"))


def _extract_seoul50plus_app_candidates(target: SiteTarget, referer_url: str) -> list[ExternalScheduleCandidate]:
    page_html = _fetch(referer_url)
    params = _seoul50plus_form_params(page_html)
    if not params:
        return []
    params["SRCH_ANN_RCRT_STAT"] = target.status_keywords[0] if target.status_keywords else "IN17003"

    candidates: list[ExternalScheduleCandidate] = []
    total_pages = 1
    for page_index in range(1, 6):
        params["pageIndex"] = str(page_index)
        payload = _fetch_json_post("https://www.50plus.or.kr/in_appListAjax", params, referer_url)
        for item in payload.get("list", []) or []:
            candidate = _candidate_from_seoul50plus_app_item(target, item)
            if candidate:
                candidates.append(candidate)
        pagination = payload.get("paginationInfo") or {}
        total_pages = int(pagination.get("totalPageCount") or total_pages)
        if page_index >= total_pages:
            break
    return _dedupe([candidate for candidate in candidates if _candidate_is_open(candidate)])[:80]


def _seoul50plus_form_params(html: str) -> dict[str, str]:
    form_match = re.search(r"<form\b[^>]*id=[\"']fpmsForm[\"'][^>]*>(.*?)</form>", html, flags=re.I | re.S)
    if not form_match:
        return {}
    params: dict[str, str] = {}
    for input_html in re.findall(r"<input\b[^>]*>", form_match.group(1), flags=re.I):
        name = _attr_value(input_html, "name")
        if not name:
            continue
        if name in params:
            continue
        params[name] = _attr_value(input_html, "value")
    return params


def _candidate_from_seoul50plus_app_item(target: SiteTarget, item: dict) -> ExternalScheduleCandidate | None:
    if target.status_keywords and str(item.get("ANN_RCRT_STAT") or "") not in target.status_keywords:
        return None
    title = _clean(str(item.get("ANN_NM") or ""))
    period = _normalize_period(str(item.get("APPDURNG_STED") or ""))
    ann_no = str(item.get("ANN_NO") or "").strip()
    if not title or not period or not ann_no:
        return None
    if target.category == "직업교육/취업훈련" and str(item.get("BIZ_SE") or "") != "IN49009":
        return None
    if target.category == "취업지원/민간채용공고" and str(item.get("BIZ_SE") or "") != "IN49008":
        return None
    return _candidate(
        target.source,
        target.category,
        title,
        period,
        f"https://www.50plus.or.kr/in_appView.do?ANN_NO={urllib.parse.quote(ann_no)}",
    )


def _extract_seoul50plus_education_candidates(
    html: str, target: SiteTarget, base_url: str
) -> list[ExternalScheduleCandidate]:
    rows = re.findall(r"<tr\b[^>]*>(.*?)</tr>", html, flags=re.I | re.S)
    candidates: list[ExternalScheduleCandidate] = []
    for row in rows:
        text = _clean(row)
        if "AI디지털교육" not in text:
            continue
        if target.status_keywords and not _matches_status(text, target.status_keywords):
            continue
        if "신청마감" in text:
            continue
        title = _text_between(text, "제목 :", "모집기간 :")
        period = _period_after_label(text, "모집기간")
        link = re.search(r"<a\b[^>]*href=[\"']([^\"']+)[\"']", row, flags=re.I | re.S)
        if not title or not period or not link:
            continue
        candidates.append(
            _candidate(target.source, target.category, _seoul_title(title, target.category), period, urllib.parse.urljoin(base_url, link.group(1)))
        )
    return _dedupe([candidate for candidate in candidates if _candidate_is_open(candidate)])[:50]


def _extract_seoul50plus_candidates(html: str, target: SiteTarget, base_url: str) -> list[ExternalScheduleCandidate]:
    anchors = re.findall(r"<a\b[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", html, flags=re.I | re.S)
    candidates: list[ExternalScheduleCandidate] = []

    for index, (href, raw_title) in enumerate(anchors):
        text = _clean(raw_title)
        period = _period_after_label(text, "모집기간")
        if not period:
            continue
        if not _matches_status(text, target.status_keywords):
            continue
        if "취업지원" in target.category and "민간채용공고" not in text and "민간채용" not in text:
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


def _extract_sba_candidates(html: str, target: SiteTarget, base_url: str) -> list[ExternalScheduleCandidate]:
    rows = re.findall(r"<tr\b[^>]*>(.*?)</tr>", html, flags=re.I | re.S)
    candidates: list[ExternalScheduleCandidate] = []
    for index, row in enumerate(rows):
        if target.status_keywords and not _matches_status(_clean(row), target.status_keywords):
            continue
        link = re.search(r"<a\b[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", row, flags=re.I | re.S)
        if not link:
            continue
        href, raw_title = link.groups()
        title = _clean(raw_title)
        period = _first_period(_clean(row))
        if not title or not period:
            continue
        candidates.append(_candidate(target.source, target.category, title, period, urllib.parse.urljoin(base_url, href)))
    return candidates[:30]


def _extract_seoul_ccei_candidates(html: str, target: SiteTarget, base_url: str) -> list[ExternalScheduleCandidate]:
    if base_url.rstrip("/").endswith("scceioi.kr"):
        return _extract_scceioi_candidates(html, target, base_url)
    candidates = _extract_ccei_json_candidates(target)
    candidates.extend(_extract_title_deadline_candidates(html, target, base_url))
    return _dedupe([candidate for candidate in candidates if _candidate_is_open(candidate)])


def _extract_ccei_json_candidates(target: SiteTarget) -> list[ExternalScheduleCandidate]:
    url = "https://ccei.creativekorea.or.kr/seoul/main/main_notice_list.json"
    request = urllib.request.Request(
        url,
        data=b"sPtime=now&kind=program",
        headers={
            "User-Agent": "Mozilla/5.0 AI-Scheduler/1.0",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=12) as response:
            payload = json.loads(response.read().decode(response.headers.get_content_charset() or "utf-8", errors="ignore"))
    except Exception:
        return []

    candidates: list[ExternalScheduleCandidate] = []
    for item in payload.get("notice_list", []):
        title = str(item.get("PROGRAM_TITLE") or item.get("TITLE") or "").strip()
        start = str(item.get("C_SDATE") or item.get("R_SDATE") or "").strip()
        end = str(item.get("C_EDATE") or item.get("R_EDATE") or "").strip()
        if not title:
            continue
        period = f"{start} ~ {end}" if start and end else _period_from_title(title)
        if not period:
            continue
        seq = str(item.get("SEQ") or "")
        menu_type = str(item.get("MENU_TYPE") or "")
        href = f"https://ccei.creativekorea.or.kr/seoul/service/program_view.do?no={seq}&sMenuType={menu_type}" if seq else settings.seoul_ccei_notice_url
        candidates.append(_candidate(target.source, target.category, title, period, href))
    return [candidate for candidate in candidates if _candidate_is_open(candidate)]


def _extract_scceioi_candidates(html: str, target: SiteTarget, base_url: str) -> list[ExternalScheduleCandidate]:
    blocks = re.findall(r"<li\b[^>]*class=[\"'][^\"']*post-item[^\"']*[\"'][^>]*>(.*?)</li>", html, flags=re.I | re.S)
    candidates: list[ExternalScheduleCandidate] = []
    for index, block in enumerate(blocks):
        title_match = re.search(r"<h3\b[^>]*>(.*?)</h3>", block, flags=re.I | re.S)
        date_match = re.search(r"<p\b[^>]*class=[\"'][^\"']*date[^\"']*[\"'][^>]*>(.*?)</p>", block, flags=re.I | re.S)
        link_match = re.search(r"<a\b[^>]*href=[\"']([^\"']+)[\"']", block, flags=re.I | re.S)
        title = _clean(title_match.group(1)) if title_match else ""
        period = _first_period(_clean(date_match.group(1))) if date_match else ""
        href = link_match.group(1) if link_match else f"{base_url}#scceioi-{index}"
        if title and period:
            candidates.append(_candidate(target.source, target.category, title, period, urllib.parse.urljoin(base_url, href)))
    return [candidate for candidate in candidates if _candidate_is_open(candidate)]


def _extract_title_deadline_candidates(html: str, target: SiteTarget, base_url: str) -> list[ExternalScheduleCandidate]:
    candidates: list[ExternalScheduleCandidate] = []
    anchors = re.findall(r"<a\b[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", html, flags=re.I | re.S)
    for index, (href, raw_title) in enumerate(anchors):
        title = _clean(raw_title)
        period = _period_from_title(title)
        if not title or not period:
            continue
        candidates.append(_candidate(target.source, target.category, title, period, urllib.parse.urljoin(base_url, href) or f"{base_url}#ccei-{index}"))
    return [candidate for candidate in candidates if _candidate_is_open(candidate)]


def _extract_kstartup_candidates(html: str, target: SiteTarget, base_url: str) -> list[ExternalScheduleCandidate]:
    lines = _html_lines(html)
    candidates: list[ExternalScheduleCandidate] = []
    seen_titles: set[str] = set()

    for index, line in enumerate(lines):
        if line.startswith("마감일자"):
            end_day = _first_date(line)
            title = _nearby_kstartup_title(lines, index)
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


def _attr_value(html: str, name: str) -> str:
    match = re.search(rf"\b{name}=[\"']([^\"']*)[\"']", html, flags=re.I)
    return unescape(match.group(1)).strip() if match else ""


def _normalize_period(value: str) -> str:
    dates = re.findall(r"20\d{2}[.\-\/]\d{1,2}[.\-\/]\d{1,2}", value)
    if len(dates) >= 2:
        return f"{_normalize_date_text(dates[0])} ~ {_normalize_date_text(dates[1])}"
    if len(dates) == 1:
        return f"마감일자 {_normalize_date_text(dates[0])}"
    return _clean(value)


def _normalize_date_text(value: str) -> str:
    parts = re.split(r"[.\-\/]", value)
    if len(parts) != 3:
        return value
    year, month, day = map(int, parts)
    return f"{year:04d}-{month:02d}-{day:02d}"


def _text_between(text: str, start_label: str, end_label: str) -> str:
    start = text.find(start_label)
    if start == -1:
        return ""
    start += len(start_label)
    end = text.find(end_label, start)
    if end == -1:
        end = len(text)
    return text[start:end].strip()


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


def _first_period(text: str) -> str:
    match = re.search(r"(20\d{2}[.\-\/]\d{1,2}[.\-\/]\d{1,2})\s*[~\-]\s*(20\d{2}[.\-\/]\d{1,2}[.\-\/]\d{1,2})", text)
    return f"{match.group(1)} ~ {match.group(2)}" if match else ""


def _period_from_title(title: str) -> str:
    match = re.search(r"[~∼]\s*(\d{1,2})[./월]\s*(\d{1,2})", title)
    if not match:
        match = re.search(r"마감\s*(\d{1,2})[./월]\s*(\d{1,2})", title)
    if not match:
        return ""
    month, day = map(int, match.groups())
    year = date.today().year
    end = date(year, month, day)
    if end < date.today():
        end = date(year + 1, month, day)
    return f"마감일자 {end:%Y-%m-%d}"


def _first_date(text: str) -> str:
    match = re.search(r"20\d{2}[.\-\/]\d{1,2}[.\-\/]\d{1,2}", text)
    return match.group(0) if match else "기간 확인 필요"


def _matches_status(text: str, keywords: tuple[str, ...]) -> bool:
    if not keywords:
        return True
    return any(keyword in text for keyword in keywords) or "오늘마감" in text


def _seoul_title(text: str, category: str) -> str:
    if "취업지원" in category:
        text = re.sub(r"^(경력인재지원|채용설명회|민간채용공고|외부채용공고)\s*", "", text)
    if "AI디지털교육" in category:
        text = re.sub(r"^\[?AI[·\s]?디지털교육\]?", "", text)
    title = re.split(r"\s+(활동비|정규직|계약직|기타|모집인원|모집기간|행사장소|무료)\s*:?", text, maxsplit=1)[0]
    return title.strip(" -·")


def _candidate_is_open(candidate: ExternalScheduleCandidate) -> bool:
    end = _candidate_end_date(candidate.recruitment_period)
    return end is None or end >= date.today()


def _candidate_end_date(period: str) -> date | None:
    matches = re.findall(r"20\d{2}[.\-\/]\d{1,2}[.\-\/]\d{1,2}", period)
    if not matches:
        return None
    raw = matches[-1].replace(".", "-").replace("/", "-")
    try:
        year, month, day = map(int, raw.split("-"))
        return date(year, month, day)
    except ValueError:
        return None


def _next_title(lines: list[str], start_index: int) -> str:
    for line in lines[start_index : start_index + 5]:
        title = line.replace("새로운게시글", "").strip()
        if title and not title.startswith("*") and "조회 " not in title:
            return title
    return ""


def _nearby_kstartup_title(lines: list[str], deadline_index: int) -> str:
    for index in range(deadline_index - 1, max(-1, deadline_index - 12), -1):
        if lines[index] == "새로운게시글" and index > 0:
            return lines[index - 1].replace("새로운게시글", "").strip()
    return _next_title(lines, deadline_index + 1)


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
