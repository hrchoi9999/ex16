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


@dataclass(frozen=True)
class CollectionResult:
    success: bool
    message: str
    candidates: list[ExternalScheduleCandidate]


def collect_interest_sites() -> CollectionResult:
    candidates: list[ExternalScheduleCandidate] = []
    errors: list[str] = []

    for source, category, url in [
        ("서울50플러스 일자리몽땅", "직업교육/취업지원", settings.seoul50plus_url),
        ("K-Startup", "모집공고", settings.kstartup_url),
    ]:
        try:
            html = _fetch(url)
            candidates.extend(_extract_candidates(html, source, category, url))
        except Exception as exc:
            errors.append(f"{source}: {exc}")

    if errors and not candidates:
        return CollectionResult(False, "관심 사이트 수집에 실패했습니다. 좌측의 수동 수집 버튼으로 다시 확인하세요.", [])
    if errors:
        return CollectionResult(True, f"{len(candidates)}개 후보를 수집했습니다. 일부 실패: {' / '.join(errors)}", candidates)
    return CollectionResult(True, f"{len(candidates)}개 후보를 수집했습니다.", candidates)


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


def _extract_candidates(html: str, source: str, category: str, base_url: str) -> list[ExternalScheduleCandidate]:
    text = re.sub(r"\s+", " ", html)
    anchors = re.findall(r"<a\b[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", text, flags=re.I | re.S)
    candidates: list[ExternalScheduleCandidate] = []
    seen: set[str] = set()

    for href, raw_title in anchors:
        title = _clean(raw_title)
        if not _looks_relevant(title, source):
            continue
        url = urllib.parse.urljoin(base_url, href)
        if url in seen:
            continue
        seen.add(url)
        period = _find_nearby_period(text, raw_title) or "모집기간 확인 필요"
        candidates.append(
            ExternalScheduleCandidate(
                id=None,
                source=source,
                category=category,
                title=title[:180],
                recruitment_period=period,
                url=url,
                status="모집중",
                collected_at=datetime.now().isoformat(timespec="seconds"),
            )
        )

    return candidates[:30]


def _clean(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value)
    value = unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def _looks_relevant(title: str, source: str) -> bool:
    if len(title) < 4:
        return False
    if source.startswith("서울50플러스"):
        return any(keyword in title for keyword in ["모집", "교육", "취업", "직업", "일자리", "참여"])
    return any(keyword in title for keyword in ["모집", "공고", "사업", "창업", "스타트업", "지원"])


def _find_nearby_period(text: str, raw_title: str) -> str:
    index = text.find(raw_title[: max(8, min(len(raw_title), 30))])
    if index < 0:
        index = 0
    window = text[max(0, index - 500) : index + 800]
    patterns = [
        r"20\d{2}[.년/-]\s*\d{1,2}[.월/-]\s*\d{1,2}일?\s*[~\-]\s*20\d{2}[.년/-]\s*\d{1,2}[.월/-]\s*\d{1,2}일?",
        r"\d{4}[.]\d{1,2}[.]\d{1,2}\s*[~\-]\s*\d{4}[.]\d{1,2}[.]\d{1,2}",
        r"모집기간[^<]{0,80}",
        r"접수기간[^<]{0,80}",
    ]
    for pattern in patterns:
        match = re.search(pattern, window)
        if match:
            return _clean(match.group(0))[:120]
    return ""
