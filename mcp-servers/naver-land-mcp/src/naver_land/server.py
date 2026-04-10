"""Naver Real Estate MCP server.

네이버 부동산(new.land.naver.com)의 현재 매물 데이터를 조회하는 MCP 서버.
국토교통부 과거 실거래가가 아닌, 지금 시장에 나와 있는 매물(호가)을 제공한다.

Tools:
  - naver_search_region: 지역명 → cortarNo 코드 변환
  - naver_get_complex_list: 지역 내 아파트 단지 목록 조회
  - naver_get_listings: 특정 단지의 현재 매물 목록 조회
  - naver_search_listings: 지역 전체 매물 검색 (단지 순회)
  - get_current_year_month: 현재 연월 (YYYYMM)
  - calculate_loan_payment: 대출 원리금 균등상환 계산
  - calculate_compound_growth: 복리 자산 증식 계산
  - calculate_monthly_cashflow: 월 현금흐름 계산
"""

from __future__ import annotations

import naver_land.tools.finance  # noqa: F401 — registers @mcp.tool()
import naver_land.tools.listings  # noqa: F401 — registers @mcp.tool()
from naver_land import mcp


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Naver Land MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help="Transport mode (default: stdio)",
    )
    parser.add_argument("--host", default="127.0.0.1", help="HTTP host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="HTTP port (default: 8000)")
    args = parser.parse_args()

    if args.transport == "http":
        import os

        import uvicorn
        from mcp.server.transport_security import TransportSecuritySettings

        mcp.settings.host = args.host
        mcp.settings.port = args.port
        mcp.settings.transport_security = TransportSecuritySettings(
            enable_dns_rebinding_protection=False,
        )
        app = mcp.streamable_http_app()
        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            proxy_headers=True,
            forwarded_allow_ips=os.environ.get("FORWARDED_ALLOW_IPS", "127.0.0.1"),
        )
    else:
        mcp.run()


if __name__ == "__main__":
    main()
