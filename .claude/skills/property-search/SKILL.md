---
name: property-search
description: "한국 부동산 아파트 월세 매물 검색, 지역별 시세 조회, 가격대별 매물 필터링. real-estate-mcp를 활용한 부동산 매물 조사 작업에 반드시 이 스킬을 사용할 것. 아파트 월세 데이터만 조회."
---

# Property Search

real-estate-mcp를 활용하여 지역별 월세 실제 매물 데이터를 수집하고 분석하는 스킬.

## 조사 워크플로우

### 1. 지역 코드 확인

```
get_region_code(query="마포구") → region_code="11440"
```

사용자가 "서울 마포구", "마포", "마포구 공덕동" 등 다양한 형태로 입력할 수 있다. get_region_code는 자유형식 텍스트를 받아 5자리 법정동 코드를 반환한다.

### 2. 데이터 수집 범위

최근 3개월 데이터를 수집한다. 이유: 단일 월 데이터는 표본이 적어 시세 왜곡 가능성이 있다.

```
get_current_year_month() → "202604"
→ 조회 대상: "202602", "202603", "202604"
```

### 3. 매물 유형별 조회

각 유형별로 월세 데이터를 수집한다:

| 도구 | 대상 | 비고 |
|------|------|------|
| `get_apartment_rent` | 아파트 | 유일하게 사용할 매물 조회 도구 |

오피스텔(`get_officetel_rent`), 빌라(`get_villa_rent`)는 사용 금지.

파라미터: `region_code`, `year_month`, `num_of_rows=100`, `min_area_sqm` (선택), `max_area_sqm` (선택)

수집 시 `monthly_rent_10k == 0`인 전세 매물은 반드시 제외하고 월세 매물만 필터링한다.

평수 필터링:
- `min_area_sqm`, `max_area_sqm`로 전용면적 범위를 지정할 수 있다 (클라이언트 측 필터링)
- 평수→㎡ 변환: 1평 = 3.3058㎡ (예: 30평 = 99.17㎡, 40평 = 132.23㎡)
- user_params.json에 `min_area_sqm`/`max_area_sqm`이 있으면 MCP 도구 호출 시 전달한다

### 4. 데이터 필터링

financial-simulation의 9가지 시나리오별 최대 금액을 기준으로 필터링한다:

- 월세: `deposit_10k <= max_wolse_deposit_10k` AND `monthly_rent_10k <= max_wolse_monthly_10k`인 매물
- 각 시나리오별로 TOP 10을 선별한다
- cashflow 계산(보증금 구성, 대출 이자, 월 총 주거비, 남은 투자금)은 수행하지 않는다 — strategy-reporter가 담당

### 5. 반환 데이터 구조

월별 원본 파일 (`02_raw/{YYYYMM}.json`):
```json
{
  "year_month": "202604",
  "region_code": "11440",
  "wolse_count": 45,
  "items": [
    {
      "unit_name": "아파트명",
      "dong": "동",
      "area_sqm": 84.5,
      "floor": 15,
      "deposit_10k": 20000,
      "monthly_rent_10k": 160,
      "build_year": 2010,
      "trade_date": "2026-04-01"
    }
  ]
}
```

시나리오별 파일 (`02_scenarios/{scenario_id}.json`):
```json
{
  "scenario_id": "목표12억_수익률2%",
  "target_asset_10k": 120000,
  "monthly_rate_pct": 2,
  "feasible": true,
  "budget": {
    "max_wolse_deposit_10k": 28811,
    "max_wolse_monthly_10k": 253
  },
  "matched_count": 42,
  "top10": [
    {
      "rank": 1, "unit_name": "아파트명", "dong": "동",
      "area_sqm": 84.5, "floor": 15,
      "deposit_10k": 20000, "monthly_rent_10k": 160,
      "build_year": 2010, "trade_date": "2026-04-01"
    }
  ]
}
```

### 6. 분석 지표

각 유형별로 다음 통계를 산출한다:

| 지표 | 설명 |
|------|------|
| 중앙값 | 보증금/월세 가격 분포의 중심 |
| 최소/최대 | 가격 범위 |
| 평수별 분포 | 20평 미만 / 20~30평 / 30평 이상 |

cashflow 계산(보증금 구성, 대출 이자, 월 총 주거비, 남은 투자금)은 strategy-reporter가 담당한다.

## 출력 형식

다중 파일 구조로 저장한다. 각 파일은 3KB 이하로 제한한다.

### 파일 구조
```
{RUN_DIR}/
├── 02_raw/
│   ├── 202602.json    # 월별 원본 월세 매물
│   ├── 202603.json
│   └── 202604.json
├── 02_scenarios/
│   ├── 목표12억_수익률2%.json   # 시나리오별 TOP 10
│   ├── 목표12억_수익률3%.json
│   └── ...
└── 02_property_research.json   # 인덱스 파일 (메타데이터 + 파일 경로 목록)
```

### 점진적 저장 규칙
1. MCP 응답을 받으면 즉시 월별 파일에 저장한다 (메모리에 쌓지 않음)
2. 시나리오별 필터링 결과도 즉시 개별 파일에 저장한다
3. 인덱스 파일은 마지막에 생성한다
4. cashflow_comment는 생성하지 않는다 — strategy-reporter가 담당

## 주의사항

- 가격 단위는 항상 만원(10k)이다. `deposit_10k: 30000` = 3억원
- 취소된 거래(`cdealType == "O"`)는 MCP에서 자동 필터링된다
- 데이터가 없는 월은 건너뛰고 가용 데이터로 분석한다
- 매물이 극히 적으면(5건 미만) 인접 지역 확대를 제안한다
