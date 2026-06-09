---
name: property-search
description: "한국 부동산 아파트 월세 매물 검색, 지역별 시세 조회, 가격대별 매물 필터링. naver-land-mcp를 활용한 부동산 매물 조사 작업에 반드시 이 스킬을 사용할 것. 아파트 월세 데이터만 조회."
---

# Property Search

naver-land-mcp를 활용하여 네이버 부동산에 현재 등록된 월세 매물 데이터를 수집하고 분석하는 스킬.

## 데이터 소스

**네이버 부동산** (new.land.naver.com) — 현재 등록된 매물(호가) 기반.
- 과거 실거래가가 아닌, 지금 시장에 나와 있는 매물을 조회한다
- 호가(asking price)이므로 실제 계약가와 다를 수 있다
- API 키 불필요

## 조사 워크플로우

### 1. 지역 코드 확인

```
naver_search_region(query="마포구") → cortar_no="1144000000"
```

사용자가 "서울 마포구", "마포", "마포구 공덕동" 등 다양한 형태로 입력할 수 있다. naver_search_region은 자유형식 텍스트를 받아 cortarNo 코드를 반환한다.

주의: 여러 결과가 반환되면 사용자에게 확인 후 선택한다.

### 2. 데이터 수집

현재 등록된 매물을 한 번에 수집한다. 시점 파라미터가 필요 없다.

```
naver_search_listings(cortar_no="1144000000", trade_type="B2")
```

- `trade_type="B2"`: 전월세 매물 조회 (월세만 필터링은 응답에서 수행)
- 응답에서 `monthly_rent_10k > 0`인 매물만 사용 (전세 제외)

**구 이름 스탬프 (`gu_name`)** — 여러 구를 조회할 때(예: "성남 전체" = 수정구/중원구/분당구), 각 구는 `naver_search_region`으로 개별 cortarNo를 얻어 따로 조회한다. 이때 **그 구에서 수집한 매물 각각에 `gu_name` 필드를 찍어 저장한다**(예: `"gu_name": "중원구"`). 매물 응답 자체에는 구 정보가 없으므로, 조회 중인 구 이름을 코드 쪽에서 스탬프해야 한다. 리포트 표에 `매물명[구명]` 형식으로 표시하는 데 쓰인다. 단일 구만 조회할 때도 그 구 이름을 찍는다.

### 3. 매물 유형별 조회

| 도구 | 대상 | 비고 |
|------|------|------|
| `naver_search_listings` | 아파트 월세 | 유일하게 사용할 매물 조회 도구 |

파라미터: `cortar_no`, `trade_type="B2"`, `min_area_sqm` (선택), `max_area_sqm` (선택), `max_complexes_per_dong=50` (동별 상한), `max_total_complexes=300` (구 전체 안전 상한)

상한은 **동 단위**로 적용된다. 응답의 `coverage.limit_reached`가 true면 누락된 동이 있다는 뜻이므로(`coverage.truncated_dongs` 확인), `max_total_complexes`를 올려 재조회를 검토한다.

수집 시 `monthly_rent_10k == 0`인 전세 매물은 반드시 제외하고 월세 매물만 필터링한다.

평수 필터링:
- `min_area_sqm`, `max_area_sqm`로 전용면적 범위를 지정할 수 있다 (MCP 도구 파라미터로 전달)
- 평수→㎡ 변환: 1평 = 3.3058㎡ (예: 30평 = 99.17㎡, 40평 = 132.23㎡)
- user_params.json에 `min_area_sqm`/`max_area_sqm`이 있으면 MCP 도구 호출 시 전달한다

### 4. 데이터 필터링

financial-simulation의 시나리오 **공격 한계선(`max_wolse_deposit_10k`)**을 1차 필터 상한으로 사용한다. 이 상한은 사용자가 감수하는 최소 달성률(`min_achievement_pct`, 기본 70%)에 해당하는 보증금 한계다:

- 월세: `deposit_10k <= max_wolse_deposit_10k` AND `monthly_rent_10k <= max_wolse_monthly_10k`인 매물
- 사용자가 월세 상한선(`max_monthly_rent_10k`)을 지정한 경우, `monthly_rent_10k <= max_monthly_rent_10k` 조건도 추가 적용
- 사용자가 사용승인일 조건(`min_use_approve_year`)을 지정한 경우, `use_approve_date`의 연도가 `min_use_approve_year` 이상인 매물만 남긴다 (준공 시점 필터)
- 1차 필터를 통과한 매물을 **보증금 내림차순(가장 공격적인 순)으로 최대 150건**까지 `listings` 배열에 담는다(파일 크기 안전 상한). `matched_count`에는 1차 필터를 통과한 **전체 건수**를 기록한다.
- 이 상한은 **거친 1차 필터**다. 매물별 실제 달성률(`min_achievement_pct` 하한) 정밀 필터와 **최종 100건 확정·달성률 구간 그룹핑**은 strategy-reporter가 cashflow 계산 후 수행한다.
- cashflow 계산(보증금 구성, 대출 이자, 월 총 주거비, 남은 투자금)은 수행하지 않는다 — strategy-reporter가 담당

### 5. 반환 데이터 구조

원본 매물 파일 (`02_raw/listings.json`):
```json
{
  "source": "naver",
  "region": { "name": "마포구", "cortar_no": "1144000000" },
  "collected_at": "2026-04-10",
  "wolse_count": 45,
  "items": [
    {
      "article_no": "12345",
      "complex_name": "래미안 마포리버뷰",
      "gu_name": "마포구",
      "article_name": "103동",
      "area_sqm": 84.5,
      "area_pyeong": 25.6,
      "floor_info": "15/25",
      "deposit_10k": 20000,
      "monthly_rent_10k": 160,
      "maintenance_fee_10k": 41,
      "direction": "남향",
      "confirm_date": "2026-04-01",
      "use_approve_date": "2018-03-01",
      "article_url": "https://new.land.naver.com/complexes/12345?articleNo=67890",
      "realtor_name": "OO공인중개사",
      "description": "매물 설명",
      "tag_list": ["역세권"]
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
  "min_achievement_pct": 70,
  "feasible": true,
  "budget": {
    "safe_wolse_deposit_10k": 28811,
    "max_wolse_deposit_10k": 51200,
    "max_wolse_monthly_10k": 253
  },
  "matched_count": 88,
  "listings": [
    {
      "rank": 1,
      "article_no": "12345",
      "complex_name": "래미안 마포리버뷰",
      "gu_name": "마포구",
      "area_sqm": 84.5,
      "area_pyeong": 25.6,
      "floor_info": "15/25",
      "deposit_10k": 20000,
      "monthly_rent_10k": 160,
      "maintenance_fee_10k": 41,
      "latitude": 37.5421,
      "longitude": 126.9389,
      "household_count": 1234,
      "confirm_date": "2026-04-01",
      "use_approve_date": "2018-03-01",
      "article_url": "https://new.land.naver.com/complexes/12345?articleNo=67890"
    }
  ]
}
```

> `listings`는 1차 필터(공격 한계선)를 통과한 매물을 보증금 내림차순으로 최대 150건까지 담은 **후보 집합**이다. strategy-reporter가 달성률을 계산해 `min_achievement_pct` 미만을 제외한 뒤, 통과 매물은 건수 제한 없이 전부 최종 확정한다(상위 N건 컷 없음). `matched_count`는 1차 필터 통과 전체 건수.

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
│   └── listings.json      # 현재 매물 전체 (월세만)
├── 02_scenarios/
│   ├── 목표12억_수익률2%.json   # 시나리오 후보 매물(listings, 공격 한계선 1차 필터, 최대 150건)
│   ├── 목표12억_수익률3%.json
│   └── ...
└── 02_property_research.json   # 인덱스 파일 (메타데이터 + 파일 경로 목록)
```

### 점진적 저장 규칙
1. naver_search_listings 응답을 받으면 즉시 파일에 저장한다 (메모리에 쌓지 않음)
2. 시나리오별 필터링 결과도 즉시 개별 파일에 저장한다
3. 인덱스 파일은 마지막에 생성한다
4. cashflow_comment는 생성하지 않는다 — strategy-reporter가 담당

## 주의사항

- 가격 단위는 항상 만원(10k)이다. `deposit_10k: 30000` = 3억원
- 네이버 매물 가격은 호가이므로 실제 계약가와 다를 수 있다
- 데이터가 없거나 `coverage.limit_reached`가 true면 `max_total_complexes`를 늘리거나 인접 지역 확대를 제안한다
- 매물이 극히 적으면(5건 미만) 인접 지역 확대를 제안한다
- 각 매물에 `article_url` (네이버 부동산 링크)이 포함되어 실제 매물을 확인할 수 있다
