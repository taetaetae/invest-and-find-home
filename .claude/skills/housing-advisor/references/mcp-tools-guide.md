# MCP 도구 레퍼런스

real-estate-mcp 서버가 제공하는 도구 중 이 하네스에서 사용하는 도구만 정리한다.

## 가격 단위

모든 가격은 만원(10,000 KRW) 단위이다.
- `price_10k: 50000` = 5억원
- `deposit_10k: 30000` = 3억원

## 지역 코드 조회

### get_region_code
- 파라미터: `query: str` (자유형식 지역명)
- 반환: `region_code` (5자리), `full_name`, `matches[]`
- 예시: `get_region_code("마포구")` → `"11440"`

## 전월세 도구

### get_apartment_rent / get_officetel_rent / get_villa_rent
- 파라미터: `region_code`, `year_month` (YYYYMM), `num_of_rows=100`
- 반환 items:
  ```json
  {
    "unit_name": "아파트명",
    "area_sqm": 84.5,
    "floor": 15,
    "deposit_10k": 30000,
    "monthly_rent_10k": 0,
    "contract_type": "전세|월세",
    "trade_date": "2025-01-15",
    "build_year": 2010
  }
  ```
- 반환 summary: `median_deposit_10k`, `min/max_deposit_10k`, `monthly_rent_avg_10k`, `sample_count`

## 매매 도구 (전세비율 계산용)

### get_apartment_trades / get_officetel_trades / get_villa_trades
- 파라미터: 전월세와 동일
- 반환 summary: `median_price_10k`, `min/max_price_10k`, `sample_count`
- 전세비율 = `rent_median_deposit / trade_median_price`

## 금융 계산 도구

### calculate_loan_payment
- 파라미터: `principal_10k`, `annual_rate_pct`, `years`
- 반환: `monthly_payment_10k`, `total_payment_10k`, `total_interest_10k`

### calculate_compound_growth
- 파라미터: `initial_10k`, `monthly_contribution_10k`, `annual_rate_pct`, `years`
- 반환: `final_value_10k`, `total_contributed_10k`, `total_gain_10k`

### calculate_monthly_cashflow
- 파라미터: `monthly_income_10k`, `monthly_loan_payment_10k`, `other_monthly_costs_10k=0`
- 반환: `monthly_cashflow_10k`

## 유틸리티

### get_current_year_month
- 파라미터: 없음
- 반환: `year_month: "202604"` (YYYYMM)

## API 키 설정

| 환경변수 | 용도 |
|---------|------|
| `DATA_GO_KR_API_KEY` | 매매/전월세 도구 (필수) |
| `ONBID_API_KEY` | 온비드 도구 (선택) |
| `ODCLOUD_API_KEY` | 청약 도구 (선택) |
