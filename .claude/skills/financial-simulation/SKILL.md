---
name: financial-simulation
description: "자산 증식 시뮬레이션, 대출 상환 계산, 월 현금흐름 분석, 월세 최대 가능 금액 산출. 투자 수익률, 대출 이자, 복리 계산, 자산 목표 달성률 등 모든 재무 시뮬레이션 작업에 반드시 이 스킬을 사용할 것."
---

# Financial Simulation

사용자의 자산, 투자 수익률, 대출 조건을 기반으로 9가지 시나리오(목표 자산 3가지 × 월 수익률 3가지)별 월세 최대 가능 금액을 산출하는 재무 시뮬레이션 스킬.

## 시뮬레이션 로직

### 1. 핵심 변수 정의

| 변수 | 설명 | 단위 |
|------|------|------|
| `total_asset` | 현재 총 자산 | 만원 |
| `target_assets` | 목표 자산 (3가지) | 만원 배열 |
| `monthly_rates` | 월 투자 수익률 (3가지) | % 배열 |
| `target_date` | 목표 달성 시점 | YYYY-MM |
| `monthly_rate` | 월 투자 수익률 (시나리오별) | % |
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

### 4. 최대 가능 금액 산출 (9가지 시나리오)

목표 자산 3가지 × 월 수익률 3가지 = 9가지 시나리오별로 최대 가능 금액을 산출한다.
각 시나리오별로 목표 일자까지 남은 개월수를 기준으로, 목표 자산에 **정확히** 도달하기 위한 최소 투자금을 역산한다.
나머지 전액 + 가용 대출 전액이 주거에 쓸 수 있는 **최대 금액(상한선)**이다.

```
남은 개월수 = target_date까지의 월수
필요 투자금 = target_asset / (1 + monthly_rate)^남은개월수
max_housing_equity = total_asset - 필요_투자금
```

월세의 경우, 매월 나가는 월세가 투자 수익을 감소시키므로:
```
max_wolse_deposit + 월세의 현가 합 ≤ max_housing_equity + 가용_대출
```

property-researcher에게는 9가지 시나리오별 **상한선**을 전달한다. 매물은 각 시나리오 상한선 이하에서 가장 비싼 순으로 선별한다.

### 6. MCP 도구 활용

- `calculate_loan_payment(principal_10k, annual_rate_pct, years)` — 대출 월 상환금
- `calculate_compound_growth(initial_10k, monthly_contribution_10k, annual_rate_pct, years)` — 복리 성장
- `calculate_monthly_cashflow(monthly_income_10k, monthly_loan_payment_10k)` — 월 현금흐름 (생활비 제외)

### 7. 대출 조건 참고 (2024~2025 기준)

한국 월세 대출 통상 조건:

| 대출 유형 | 한도 | 금리 범위 |
|----------|------|----------|
| 월세대출 (청년) | 월 최대 40만원 | 연 1.3~1.5% |

최신 금리는 WebSearch로 확인하여 보정한다.

## 출력 형식

`_workspace/01_financial_simulation.json` 에 저장:

```json
{
  "input_params": {
    "total_asset_10k": 0,
    "target_assets_10k": [0, 0, 0],
    "target_date": "YYYY-MM",
    "monthly_rates_pct": [0, 0, 0],
    "months_remaining": 0,
    "company_interest_support": {}
  },
  "scenarios": [
    {
      "scenario_id": "목표A_수익률X",
      "target_asset_10k": 0,
      "monthly_rate_pct": 0,
      "budget": {
        "required_investment_10k": 0,
        "max_housing_equity_10k": 0,
        "available_loans": [
          { "source": "본인회사", "amount_10k": 0, "effective_rate_pct": 0 },
          { "source": "배우자회사", "amount_10k": 0, "effective_rate_pct": 0 }
        ],
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
