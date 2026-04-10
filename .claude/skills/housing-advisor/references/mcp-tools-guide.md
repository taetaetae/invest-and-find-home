# MCP 도구 레퍼런스

naver-land-mcp 서버가 제공하는 도구 중 이 하네스에서 사용하는 도구만 정리한다.

## 데이터 소스

**네이버 부동산** (new.land.naver.com) — 현재 등록된 매물(호가) 기반.
- 실시간 매물: 중개사가 등록한 현재 매물을 조회한다 (과거 실거래가가 아님)
- 호가: 매물 가격은 호가(asking price)이므로 실제 계약가와 다를 수 있다
- API 키 불필요: HTTP 헤더만으로 접근한다

## 가격 단위

모든 가격은 만원(10,000 KRW) 단위이다.
- `deposit_10k: 50000` = 5억원
- `monthly_rent_10k: 160` = 160만원

## 지역 코드 조회

### naver_search_region
- 파라미터: `query: str` (자유형식 지역명)
- 반환: `regions[]` — 각 항목에 `cortar_no`, `cortar_name`, `cortar_type`
- 예시: `naver_search_region("마포구")` → cortarNo `"1144000000"`
- 참고: cortarNo는 10자리 (국토교통부 5자리와 다름)

## 매물 조회 도구

### naver_search_listings (주력 도구)
- 지역 전체 매물을 단지 순회로 검색한다
- 파라미터:
  - `cortar_no: str` — 지역 코드 (naver_search_region에서 획득)
  - `trade_type: str = "B2"` — B2=전월세, B3=월세
  - `min_area_sqm: float | None` — 최소 전용면적 (㎡)
  - `max_area_sqm: float | None` — 최대 전용면적 (㎡)
  - `max_complexes: int = 50` — 조회할 최대 단지 수
- 반환:
  - `total_count`: 전체 매물 수
  - `wolse_count`: 월세 매물 수 (monthly_rent_10k > 0)
  - `items[]`: 매물 리스트 (통일 포맷)
  - `summary`: 통계 (median/min/max)

### naver_get_complex_list
- 특정 지역의 아파트 단지 목록 조회
- 파라미터: `cortar_no: str`, `trade_type: str = "B2"`
- 반환: `complexes[]` — 각 항목에 `complex_no`, `complex_name`, `total_units`

### naver_get_listings
- 특정 단지의 현재 매물 조회
- 파라미터: `complex_no: str`, `trade_type: str = "B2"`, `page: int = 1`
- 반환: `articles[]` (통일 포맷), `is_more_data: bool`

## 매물 데이터 통일 포맷

```json
{
  "article_no": "매물번호",
  "complex_name": "단지명",
  "article_name": "매물명",
  "area_sqm": 84.5,
  "area_pyeong": 25.6,
  "floor_info": "15/25",
  "deposit_10k": 20000,
  "monthly_rent_10k": 160,
  "direction": "남향",
  "confirm_date": "2026-04-01",
  "article_url": "https://new.land.naver.com/complexes/12345?articleNo=67890",
  "realtor_name": "OO공인중개사",
  "description": "매물 설명",
  "tag_list": ["역세권", "주차가능"]
}
```

## 금융 계산 도구

### calculate_loan_payment
- 파라미터: `principal_10k`, `annual_rate_pct`, `years`
- 반환: `monthly_payment_10k`, `total_payment_10k`, `total_interest_10k`

### calculate_compound_growth
- 파라미터: `initial_10k`, `monthly_contribution_10k`, `annual_rate_pct`, `years`
- 반환: `final_value_10k`, `total_contributed_10k`, `total_gain_10k`

### calculate_monthly_cashflow
- 파라미터: `monthly_income_10k`, `monthly_loan_payment_10k`, `monthly_living_cost_10k`, `other_monthly_costs_10k=0`
- 반환: `monthly_cashflow_10k`

## 유틸리티

### get_current_year_month
- 파라미터: 없음
- 반환: `year_month: "202604"` (YYYYMM)
