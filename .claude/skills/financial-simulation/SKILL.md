---
name: financial-simulation
description: "자산 증식 시뮬레이션, 대출 상환 계산, 월 현금흐름 분석, 월세 최대 가능 금액 산출. 투자 수익률, 대출 이자, 복리 계산, 자산 목표 달성률 등 모든 재무 시뮬레이션 작업에 반드시 이 스킬을 사용할 것."
---

# Financial Simulation

사용자의 자산, 투자 수익률, 대출 조건을 기반으로 단일 시나리오(목표 자산 1개 × 월 수익률 1개)의 월세 최대 가능 금액을 산출하는 재무 시뮬레이션 스킬.

## 시뮬레이션 로직

### 1. 핵심 변수 정의

| 변수 | 설명 | 단위 |
|------|------|------|
| `total_asset` | 현재 총 자산 | 만원 |
| `target_asset` | 목표 자산 | 만원 |
| `monthly_rate` | 월 투자 수익률 | % |
| `target_date` | 목표 달성 시점 | YYYY-MM |
| `loan_amount` | 대출 금액 | 만원 |
| `loan_rate` | 대출 이자율 | 연 % |
| `company_support_loan_limit` | 회사 이자 지원 대상 대출 한도 | 만원 |
| `company_supported_rate` | 회사가 지원하는 이자율 | 연 % |

### 2. 전세 관련 — 제거됨 (월세만 분석)

### 3. 월세 최대 가능 금액 산출

월세의 경우, 보증금이 적은 대신 매월 월세가 나간다. 월세는 투자 수익에서 차감된다:

```
실질 월 수익 = 투자금 × 월수익률 - 월세 - 대출 월 상환금
```

거주 기간 동안 실질 월 수익이 자산 증식에 기여하므로, 월세가 높을수록 자산 증식이 느려진다.

### 4. 최대 가능 금액 산출 (단일 시나리오 + 달성률 하한)

목표 자산 1개 × 월 수익률 1개 = 단일 시나리오의 최대 가능 금액을 산출한다.
목표 일자까지 남은 개월수를 기준으로 **두 개의 보증금 상한선**을 산출한다.

**(1) 안전선 (목표 100% 정확히 달성)**
목표 자산에 **정확히** 도달하기 위한 최소 투자금을 역산한다. 나머지 전액 + 가용 대출 전액이 안전선 보증금이다.
```
남은 개월수 = target_date까지의 월수
필요 투자금(100%) = target_asset / (1 + monthly_rate)^남은개월수
max_housing_equity(100%) = total_asset - 필요_투자금(100%)
safe_wolse_deposit = max_housing_equity(100%) + 가용_대출   (월세 현가 보정 후)
```

**(2) 공격 한계선 (목표의 `min_achievement_pct`%까지 허용)**
사용자가 목표 미달을 감수하는 하한 달성률(`min_achievement_pct`, 기본 70). 목표의 그 비율까지만 도달하면 되므로 더 적은 투자금으로 충분 → 더 큰 보증금이 가능하다.
```
필요 투자금(하한) = (target_asset × min_achievement_pct/100) / (1 + monthly_rate)^남은개월수
max_housing_equity(하한) = total_asset - 필요_투자금(하한)
max_wolse_deposit = max_housing_equity(하한) + 가용_대출   (월세 현가 보정 후)
```

월세의 경우 매월 나가는 월세가 투자 수익을 감소시키므로 두 상한 모두 월세 현가 합을 차감해 보정한다:
```
보증금 + 월세의 현가 합 ≤ max_housing_equity + 가용_대출
```

property-researcher에게는 **공격 한계선(`max_wolse_deposit`)**을 1차 필터 상한으로 전달한다. 매물은 이 상한 이하에서 수집하고, strategy-reporter가 매물별 실제 달성률을 계산해 `min_achievement_pct` 미만은 최종 제외한다. `safe_wolse_deposit`(안전선)은 리포트 전략 요약(matrix)에 참고용으로 표기한다.

`min_achievement_pct`가 100이면 두 상한선은 같아진다(기존 동작과 동일).

### 6. MCP 도구 활용

- `calculate_loan_payment(principal_10k, annual_rate_pct, years)` — 대출 월 상환금
- `calculate_compound_growth(initial_10k, monthly_contribution_10k, annual_rate_pct, years)` — 복리 성장
- `calculate_monthly_cashflow(monthly_income_10k, monthly_loan_payment_10k)` — 월 현금흐름 (생활비 제외)

## 출력 형식

`_workspace/01_financial_simulation.json` 에 저장:

```json
{
  "input_params": {
    "total_asset_10k": 0,
    "target_asset_10k": 0,
    "target_date": "YYYY-MM",
    "monthly_rate_pct": 0,
    "months_remaining": 0,
    "company_interest_support": {}
  },
  "scenarios": [
    {
      "scenario_id": "목표A_수익률X",
      "target_asset_10k": 0,
      "monthly_rate_pct": 0,
      "min_achievement_pct": 70,
      "budget": {
        "required_investment_10k": 0,
        "max_housing_equity_10k": 0,
        "available_loans": [
          { "source": "본인회사", "amount_10k": 0, "effective_rate_pct": 0 },
          { "source": "배우자회사", "amount_10k": 0, "effective_rate_pct": 0 }
        ],
        "safe_wolse_deposit_10k": 0,
        "max_wolse_deposit_10k": 0,
        "max_wolse_monthly_10k": 0
      }
    }
  ],
  "projection": {
    "description": "각 매물별 예상 자산은 property-researcher가 매물 가격 기반으로 계산"
  }
}
```

### budget 필드 범례

| 필드 | 의미 |
|------|------|
| `min_achievement_pct` | 사용자가 감수하는 최소 목표 달성률(%). `user_params.json`에서 읽음. 기본 70 |
| `required_investment_10k` | 안전선(100% 달성)에 필요한 최소 투자금 |
| `max_housing_equity_10k` | 안전선 기준 주거에 쓸 수 있는 자기자본 |
| `safe_wolse_deposit_10k` | **안전선** 보증금 상한(100% 달성). 리포트 matrix 참고용 |
| `max_wolse_deposit_10k` | **공격 한계선** 보증금 상한(`min_achievement_pct`% 달성). property-researcher가 1차 필터에 사용 |
| `max_wolse_monthly_10k` | 월세 월납 상한 (사용자 `max_monthly_rent_10k` 또는 시뮬레이션 산출값) |

> `min_achievement_pct`를 낮출수록 `max_wolse_deposit_10k`(공격 한계선)이 커져 더 비싼 매물까지 후보에 들어온다. 100이면 안전선과 동일.
