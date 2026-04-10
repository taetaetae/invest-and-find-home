"""네이버 부동산 API 클라이언트.

네이버 부동산(new.land.naver.com) API를 호출하여
현재 등록된 매물 데이터를 조회한다.

인증 흐름:
  1. Playwright(headless Chrome)로 메인 페이지 방문 → JS가 JWT 토큰 자동 생성
  2. JWT 토큰 + 쿠키를 추출
  3. curl_cffi(Chrome TLS 핑거프린트)로 API 호출

제한사항:
  - Playwright + Chromium이 설치되어 있어야 한다
  - JWT 토큰은 약 3시간 유효 (exp 기준)
"""

from __future__ import annotations

import asyncio
import time as _time
from typing import Any
from urllib.parse import urlencode

from curl_cffi import requests as curl_requests

BASE_URL = "https://new.land.naver.com"

_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
}

_REQUEST_DELAY = 0.5

# 세션 상태
_jwt_token: str | None = None
_cookies: dict[str, str] = {}
_session_init_time: float = 0
_SESSION_TTL = 7200  # 2시간마다 세션 갱신


async def _init_session() -> None:
    """Playwright로 브라우저를 띄워 JWT 토큰과 쿠키를 획득한다."""
    global _jwt_token, _cookies, _session_init_time
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
        )
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1920, "height": 1080},
            locale="ko-KR",
        )
        await context.add_init_script(
            'Object.defineProperty(navigator, "webdriver", { get: () => undefined });'
        )
        page = await context.new_page()

        token = None

        async def on_request(request: Any) -> None:
            nonlocal token
            auth = request.headers.get("authorization", "")
            if auth.startswith("Bearer ") and token is None:
                token = auth

        page.on("request", on_request)

        await page.goto(
            f"{BASE_URL}/complexes/1576",
            wait_until="networkidle",
            timeout=30000,
        )
        await page.wait_for_timeout(3000)

        cookies_list = await context.cookies()
        _cookies = {
            c["name"]: c["value"]
            for c in cookies_list
            if "land.naver" in c.get("domain", "")
        }
        _jwt_token = token
        _session_init_time = _time.time()

        await browser.close()


async def _ensure_session() -> None:
    """세션이 유효한지 확인하고, 필요 시 갱신한다."""
    now = _time.time()
    if _jwt_token is None or (now - _session_init_time) > _SESSION_TTL:
        await _init_session()


def _get_sync(url: str, referer: str | None = None) -> Any:
    """curl_cffi로 동기 GET 요청."""
    headers = {**_HEADERS}
    if _jwt_token:
        headers["Authorization"] = _jwt_token
    if referer:
        headers["Referer"] = referer
    else:
        headers["Referer"] = f"{BASE_URL}/complexes"

    resp = curl_requests.get(
        url,
        headers=headers,
        cookies=_cookies,
        impersonate="chrome136",
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


async def _get(path: str, params: dict[str, Any] | None = None, referer: str | None = None) -> Any:
    """비동기 API GET 요청."""
    await _ensure_session()
    url = f"{BASE_URL}/api{path}"
    if params:
        url = f"{url}?{urlencode(params)}"
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _get_sync, url, referer)


# ── 지역 조회 ──


async def get_cortars(cortar_no: str) -> dict[str, Any]:
    """cortarNo로 지역 정보를 조회한다."""
    return await _get("/cortars", params={"cortarNo": cortar_no})


async def get_region_list(cortar_no: str) -> list[dict[str, Any]]:
    """특정 지역의 하위 동 목록을 조회한다."""
    data = await _get("/regions/list", params={"cortarNo": cortar_no})
    return data.get("regionList", [])


async def get_complex_list(
    cortar_no: str,
    trade_type: str = "B2",
) -> list[dict[str, Any]]:
    """특정 동의 아파트 단지 목록을 조회한다."""
    data = await _get(
        "/regions/complexes",
        params={
            "cortarNo": cortar_no,
            "realEstateType": "APT",
            "tradeType": trade_type,
        },
    )
    return data.get("complexList", [])


# ── 매물 조회 ──


async def get_articles(
    complex_no: str,
    trade_type: str = "B2",
    page: int = 1,
) -> dict[str, Any]:
    """특정 단지의 현재 매물 목록을 조회한다."""
    params = {
        "realEstateType": "APT",
        "tradeType": trade_type,
        "page": str(page),
        "sameAddressGroup": "true",
        "sortedBy": "prc",
    }
    referer = f"{BASE_URL}/complexes/{complex_no}"
    data = await _get(f"/articles/complex/{complex_no}", params=params, referer=referer)
    return data


def _parse_article(article: dict[str, Any], complex_name: str, complex_no: str = "") -> dict[str, Any]:
    """네이버 매물 응답을 통일 포맷으로 변환한다."""
    deposit_10k = _parse_price(article.get("dealOrWarrantPrc", "0"))
    monthly_rent_10k = _parse_price(article.get("rentPrc", "0"))

    area2 = article.get("area2", 0)
    area_sqm = float(area2) if area2 else 0.0
    area_pyeong = round(area_sqm / 3.3058, 1)

    article_no = article.get("articleNo", "")
    building_name = article.get("buildingName", "")
    direction = article.get("direction", "")
    confirm_ymd = article.get("articleConfirmYmd", "")

    # display_name: "판교퍼스트힐푸르지오 104동, 남향, 2026.04.08"
    parts = [complex_name]
    if building_name:
        parts[0] = f"{complex_name} {building_name}"
    detail_parts = []
    if direction:
        detail_parts.append(direction)
    if confirm_ymd and len(confirm_ymd) == 8:
        detail_parts.append(f"{confirm_ymd[:4]}.{confirm_ymd[4:6]}.{confirm_ymd[6:]}")
    display_name = parts[0]
    if detail_parts:
        display_name += ", " + ", ".join(detail_parts)

    return {
        "article_no": article_no,
        "complex_no": complex_no,
        "complex_name": complex_name,
        "display_name": display_name,
        "article_name": article.get("articleName", ""),
        "building_name": building_name,
        "area_sqm": area_sqm,
        "area_pyeong": area_pyeong,
        "floor_info": article.get("floorInfo", ""),
        "deposit_10k": deposit_10k,
        "monthly_rent_10k": monthly_rent_10k,
        "direction": direction,
        "confirm_date": confirm_ymd,
        "article_url": f"https://new.land.naver.com/complexes/{complex_no}?articleNo={article_no}",
        "realtor_name": article.get("realtorName", ""),
        "description": article.get("articleFeatureDesc", ""),
        "tag_list": article.get("tagList", []),
        "trade_type_name": article.get("tradeTypeName", ""),
    }


def _parse_price(price_str: str) -> int:
    """네이버 가격 문자열을 만원 단위 정수로 변환한다.

    예: "5억 3,000" → 53000, "3,000" → 3000, "15억" → 150000
    """
    if not price_str or price_str.strip() == "" or price_str == "0":
        return 0

    price_str = price_str.strip().replace(",", "")
    total = 0

    if "억" in price_str:
        parts = price_str.split("억")
        eok_part = parts[0].strip()
        total += int(eok_part) * 10000
        remainder = parts[1].strip() if len(parts) > 1 else ""
        if remainder:
            total += int(remainder)
    else:
        try:
            total = int(price_str)
        except ValueError:
            return 0

    return total


# ── 지역 전체 매물 검색 ──


async def search_listings(
    division_cortar_no: str,
    trade_type: str = "B2",
    min_area_sqm: float | None = None,
    max_area_sqm: float | None = None,
    max_complexes: int = 50,
) -> list[dict[str, Any]]:
    """구/군 단위 지역의 전체 동을 순회하여 월세 매물을 수집한다.

    Args:
        division_cortar_no: 구/군 단위 지역 코드 (예: "4113500000")
        trade_type: 거래유형 — B2=전월세
        min_area_sqm: 최소 전용면적 (㎡)
        max_area_sqm: 최대 전용면적 (㎡)
        max_complexes: 조회할 최대 단지 수

    Returns:
        통일 포맷의 매물 리스트
    """
    dongs = await get_region_list(division_cortar_no)
    all_listings: list[dict[str, Any]] = []
    complex_count = 0

    for dong in dongs:
        dong_no = dong.get("cortarNo", "")
        if not dong_no:
            continue

        await asyncio.sleep(_REQUEST_DELAY)

        try:
            complexes = await get_complex_list(dong_no, trade_type)
        except Exception:
            continue

        # rentCount > 0인 단지만 매물 조회
        rent_complexes = [c for c in complexes if c.get("rentCount", 0) > 0]

        for cpx in rent_complexes:
            if complex_count >= max_complexes:
                break

            complex_no = cpx.get("complexNo", "")
            complex_name = cpx.get("complexName", "")
            if not complex_no:
                continue

            await asyncio.sleep(_REQUEST_DELAY)
            complex_count += 1

            try:
                data = await get_articles(complex_no, trade_type, page=1)
            except Exception:
                continue

            article_list = data.get("articleList", [])
            for article in article_list:
                parsed = _parse_article(article, complex_name, complex_no)

                # 면적 필터
                if min_area_sqm and parsed["area_sqm"] < min_area_sqm:
                    continue
                if max_area_sqm and parsed["area_sqm"] > max_area_sqm:
                    continue

                all_listings.append(parsed)

        if complex_count >= max_complexes:
            break

    return all_listings
