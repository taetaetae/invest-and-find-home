"""MCP tools for Naver Real Estate listing search."""

from __future__ import annotations

from typing import Any

from naver_land import mcp
from naver_land.naver_api import (
    get_articles,
    get_complex_detail,
    get_complex_list,
    get_cortars,
    get_region_list,
    search_listings,
    _match_maintenance_fee,
    _parse_article,
)


@mcp.tool()
async def naver_search_region(query: str) -> dict[str, Any]:
    """Search region by cortarNo to get region info.

    네이버 부동산은 cortarNo(10자리 지역 코드)를 사용한다.
    주요 지역 코드:
      - 서울 마포구: 1144000000
      - 서울 강남구: 1168000000
      - 성남 분당구: 4113500000
      - 서울 서초구: 1165000000

    Args:
        query: cortarNo (10자리 지역 코드)

    Returns:
        region info with cortarNo, cortarName, cityName, etc.
    """
    try:
        data = await get_cortars(query)
        return {
            "cortar_no": data.get("cortarNo", ""),
            "cortar_name": data.get("cortarName", ""),
            "city_name": data.get("cityName", ""),
            "division_name": data.get("divisionName", ""),
            "cortar_type": data.get("cortarType", ""),
            "center_lat": data.get("centerLat", 0),
            "center_lon": data.get("centerLon", 0),
        }
    except Exception as e:
        return {"error": "search_failed", "message": str(e)}


@mcp.tool()
async def naver_get_region_list(cortar_no: str) -> dict[str, Any]:
    """Get sub-region (dong) list for a district.

    Args:
        cortar_no: District-level cortarNo (e.g. "4113500000" for 분당구)

    Returns:
        regions: List of sub-regions with cortarNo, cortarName
    """
    try:
        regions = await get_region_list(cortar_no)
        return {
            "count": len(regions),
            "regions": [
                {
                    "cortar_no": r.get("cortarNo", ""),
                    "cortar_name": r.get("cortarName", ""),
                    "cortar_type": r.get("cortarType", ""),
                }
                for r in regions
            ],
        }
    except Exception as e:
        return {"error": "failed", "message": str(e)}


@mcp.tool()
async def naver_get_complex_list(
    cortar_no: str,
    trade_type: str = "B2",
) -> dict[str, Any]:
    """Get apartment complex list in a dong-level region.

    Args:
        cortar_no: Dong-level cortarNo (e.g. "4113510800" for 정자동)
        trade_type: B1=매매, B2=전월세

    Returns:
        complexes: List of complexes with complex_no, name, rent_count, etc.
    """
    try:
        results = await get_complex_list(cortar_no, trade_type)
        return {
            "count": len(results),
            "complexes": [
                {
                    "complex_no": c.get("complexNo", ""),
                    "complex_name": c.get("complexName", ""),
                    "total_units": c.get("totalHouseholdCount", 0),
                    "completed_ymd": c.get("useApproveYmd", ""),
                    "deal_count": c.get("dealCount", 0),
                    "lease_count": c.get("leaseCount", 0),
                    "rent_count": c.get("rentCount", 0),
                    "address": c.get("cortarAddress", ""),
                }
                for c in results
            ],
        }
    except Exception as e:
        return {"error": "failed", "message": str(e)}


@mcp.tool()
async def naver_get_listings(
    complex_no: str,
    trade_type: str = "B2",
    page: int = 1,
) -> dict[str, Any]:
    """Get current listings for a specific apartment complex.

    Args:
        complex_no: Complex number from naver_get_complex_list
        trade_type: B1=매매, B2=전월세
        page: Page number (default 1)

    Returns:
        articles: List of listings with deposit, monthly rent, area, etc.
        is_more_data: Whether more pages exist
    """
    try:
        # 단지 상세에서 평형별 관리비 조회
        pyeong_detail_list: list[dict[str, Any]] = []
        try:
            detail = await get_complex_detail(complex_no)
            pyeong_detail_list = detail.get("complexPyeongDetailList", [])
        except Exception:
            pass

        data = await get_articles(complex_no, trade_type, page)
        article_list = data.get("articleList", [])
        complex_name = article_list[0].get("articleName", "") if article_list else ""

        articles = []
        for a in article_list:
            parsed = _parse_article(a, complex_name, complex_no)
            parsed["maintenance_fee_10k"] = _match_maintenance_fee(
                pyeong_detail_list, parsed["area_name"], parsed["area_sqm"],
            )
            articles.append(parsed)

        return {
            "count": len(articles),
            "is_more_data": data.get("isMoreData", False),
            "articles": articles,
        }
    except Exception as e:
        return {"error": "failed", "message": str(e)}


@mcp.tool()
async def naver_search_listings(
    cortar_no: str,
    trade_type: str = "B2",
    min_area_sqm: float | None = None,
    max_area_sqm: float | None = None,
    max_complexes: int = 50,
) -> dict[str, Any]:
    """Search all current listings in a district (iterates through dongs and complexes).

    This is the primary tool for collecting rental listings.
    It iterates through all dongs in the district, finds complexes with rentCount > 0,
    and collects their listings.

    Args:
        cortar_no: District-level cortarNo (e.g. "4113500000" for 분당구)
        trade_type: B2=전월세 (default)
        min_area_sqm: Minimum exclusive area in sqm (optional)
        max_area_sqm: Maximum exclusive area in sqm (optional)
        max_complexes: Max complexes to query (default 50)

    Returns:
        total_count: Total listings found
        wolse_count: Listings with monthly_rent > 0
        items: Wolse-only listings in unified format
        summary: Statistics (median/min/max deposit and rent)
    """
    try:
        listings = await search_listings(
            cortar_no, trade_type, min_area_sqm, max_area_sqm, max_complexes
        )

        # 월세만 필터 (monthly_rent_10k > 0)
        wolse_items = [item for item in listings if item["monthly_rent_10k"] > 0]

        summary = _build_summary(wolse_items)

        return {
            "total_count": len(listings),
            "wolse_count": len(wolse_items),
            "items": wolse_items,
            "summary": summary,
        }
    except Exception as e:
        return {"error": "failed", "message": str(e)}


def _build_summary(items: list[dict[str, Any]]) -> dict[str, Any]:
    """매물 리스트에서 통계를 산출한다."""
    if not items:
        return {
            "median_deposit_10k": 0,
            "min_deposit_10k": 0,
            "max_deposit_10k": 0,
            "median_monthly_rent_10k": 0,
            "min_monthly_rent_10k": 0,
            "max_monthly_rent_10k": 0,
            "median_maintenance_fee_10k": 0,
            "min_maintenance_fee_10k": 0,
            "max_maintenance_fee_10k": 0,
            "sample_count": 0,
        }

    deposits = sorted(item["deposit_10k"] for item in items)
    rents = sorted(item["monthly_rent_10k"] for item in items)
    fees = sorted(item.get("maintenance_fee_10k", 0) for item in items)
    n = len(items)
    mid = n // 2

    return {
        "median_deposit_10k": deposits[mid] if n % 2 else (deposits[mid - 1] + deposits[mid]) // 2,
        "min_deposit_10k": deposits[0],
        "max_deposit_10k": deposits[-1],
        "median_monthly_rent_10k": rents[mid] if n % 2 else (rents[mid - 1] + rents[mid]) // 2,
        "min_monthly_rent_10k": rents[0],
        "max_monthly_rent_10k": rents[-1],
        "median_maintenance_fee_10k": fees[mid] if n % 2 else (fees[mid - 1] + fees[mid]) // 2,
        "min_maintenance_fee_10k": fees[0],
        "max_maintenance_fee_10k": fees[-1],
        "sample_count": n,
    }


@mcp.tool()
def get_current_year_month() -> dict[str, str]:
    """Return the current year and month in YYYYMM format.

    Returns:
        year_month: Current year-month string (e.g. "202604")
    """
    from datetime import datetime, timezone

    now = datetime.now(tz=timezone.utc)
    return {"year_month": now.strftime("%Y%m")}
