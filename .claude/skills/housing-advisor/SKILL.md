---
name: housing-advisor
description: "부동산 월세 전략 어드바이저. 자산 증식 목표, 대출 조건, 투자 수익률을 기반으로 최적의 주거 전략을 분석하고 실제 매물 기반 HTML 리포트를 생성. '시작하자', '시작', '해줘', '분석해줘', '집 구하기', '월세 전략', '주거 전략', '이사 계획', '월세 리포트', '부동산 시뮬레이션', '주거비 분석' 요청 시 반드시 이 스킬을 사용할 것. 이 프로젝트에서 사용자가 대화를 시작하면 무조건 이 스킬을 트리거한다."
---

# Housing Advisor — 부동산 월세 전략 오케스트레이터

목표 자산 달성률 하한(`min_achievement_pct`, 기본 70%) 이상 범위에서, 더 비싼 집(달성률 낮음)부터 안전한 선택(달성률 높음)까지 **달성률 구간별로 월세 매물을 최대 100건** 추천하는 에이전트 팀 오케스트레이터.

## 실행 모드: 에이전트 팀

## 에이전트 구성

| 팀원 | 에이전트 정의 | subagent_type | 역할 | 스킬 | 출력 |
|------|-------------|---------------|------|------|------|
| financial-planner | `.claude/agents/financial-planner.md` | general-purpose | 재무 시뮬레이션 | financial-simulation | `{RUN_DIR}/01_financial_simulation.json` |
| property-researcher | `.claude/agents/property-researcher.md` | general-purpose | 매물 조사 | property-search | `{RUN_DIR}/02_property_research.json` |
| strategy-reporter | `.claude/agents/strategy-reporter.md` | general-purpose | 전략 종합 + 리포트 | strategy-report | `{RUN_DIR}/housing_report.html` |

모든 에이전트는 `model: "opus"` 로 호출한다.

## 워크플로우

### Phase 1: 대화형 단계별 입력 수집

**실행 시작 시 타임스탬프 디렉토리 생성:**
매 실행마다 `_workspace/YYYY-MM-DD_HHmm/` 형태의 새 디렉토리를 생성한다. (예: `_workspace/2026-04-09_2247/`)
이후 모든 산출물은 이 디렉토리 안에 저장한다. 이전 실행 결과는 그대로 보존되어 과거 분석과 비교할 수 있다.

```bash
# 실행 시작 시 Bash로 타임스탬프 디렉토리 생성
RUN_DIR="_workspace/$(date '+%Y-%m-%d_%H%M')"
mkdir -p "$RUN_DIR/00_input"
```

이후 모든 파일 경로에서 `_workspace/`를 `_workspace/YYYY-MM-DD_HHmm/`으로 대체한다.
에이전트 프롬프트에 `RUN_DIR` 경로를 전달하여 모든 팀원이 같은 디렉토리에 저장하도록 한다.

사용자와 자연스러운 대화를 통해 단계별로 정보를 수집한다. 한꺼번에 모든 정보를 요구하지 않고, 각 단계에서 1~2개씩 물어보며 맥락을 쌓아간다. 사용자가 처음 트리거하면 인사와 함께 첫 질문을 시작한다.

**중요: AskUserQuestion 도구를 사용하지 않는다.** 모든 질문은 일반 텍스트 메시지로 출력하고, 사용자의 자유 입력 응답을 기다린다. 이유: 자산 금액, 수익률, 지역명 등은 선택지로 제한할 수 없는 자유 입력이다.

**Step 1: 현재 자산과 목표**

> "안녕하세요! 자산 증식과 주거, 두 마리 토끼를 잡아보겠습니다.
> 먼저 현재 상황부터 알려주세요.
> - 현재 총 자산은 얼마인가요? (예: 3억)
> - 목표 자산은 얼마인가요? (예: 20억)
> - 목표 달성 시점은 언제인가요? (예: 2027년 12월)"

→ `total_asset_10k`, `target_asset_10k` (단일 값), `target_date` 수집

**Step 2: 투자 수익률**

> "월 수익률을 가정해주세요.
> (예: 월 2%)"

→ `monthly_rate_pct` (단일 값) 수집
→ 목표 자산 1개 × 월 수익률 1개 = 단일 시나리오로 분석합니다.

**Step 2-B: 최소 목표 달성률 (옵션)**

> "목표 자산에 100% 도달하는 안전한 선택뿐 아니라, 목표에 다소 못 미쳐도 더 좋은(비싼) 집까지 보고 싶으실 수 있습니다.
> 감수할 수 있는 **최소 목표 달성률**을 알려주세요. (예: 70% — 목표의 70%까지는 감수)
> 기본값은 70%입니다. 100%로 하면 목표를 정확히 달성하는 매물만 봅니다."

→ `min_achievement_pct` 수집 (기본 70, 정수 %). 매물은 달성률이 이 값 이상인 것만 추천하며, 달성률 구간(🟢안전 ≥100 / 🟡절충 85~100 / 🔴공격 하한~85)으로 묶어 비교한다. 100이면 목표 정확 달성 매물만(기존 동작).

**Step 3: 회사 이자 지원 (옵션)**

> "혹시 회사에서 주거 대출 이자 지원이 있나요?
> 있다면 이자 지원 대상 대출 한도와 회사가 지원하는 이자율을 알려주세요.
> (예: 대출 최대 1억까지 연 2% 이자 지원 / 없으면 '없음')
> 참고: 회사가 직접 대출해주는 게 아니라, 은행 대출 이자를 회사가 일부 부담해주는 방식입니다."

→ `company_interest_support` 수집. "없음"이면 `{ "available": false }`
→ 있으면: `{ "available": true, "loan_limit_10k": 한도, "supported_rate_pct": 회사지원이자율 }`
→ 실질 이자 부담 = 은행 대출 이자율 - 회사 지원 이자율

**Step 4: 희망 지역과 평수**

> "어떤 지역에서 집을 알아보고 계신가요?
> 그리고 희망하는 평수 범위가 있으면 알려주세요.
> (예: 서울 마포구, 30평 이상 / 성남 분당구, 25~35평)"

→ `region` 수집. `housing_type`은 `"월세"`로 고정한다. 월세 매물을 분석하여 달성률 구간별 최대 100건을 추천한다.
→ `min_area_pyeong`, `max_area_pyeong` 수집 (선택). 미지정 시 null.
→ 평수→㎡ 변환: 1평 = 3.3058㎡. `min_area_sqm = min_area_pyeong * 3.3058`, `max_area_sqm = max_area_pyeong * 3.3058`

**Step 5: 사용승인일(준공 시점) 조건 (옵션)**

> "사용승인일(아파트 준공 시점) 조건이 있나요?
> 특정 연도 이후 준공된 매물만 보거나, 제한 없이 모두 볼 수 있습니다.
> (예: 2000년 이후만 / 2010년 이후만 / 제한 없음)"

→ `min_use_approve_year` 수집. "제한 없음"이면 `null`
→ 있으면: 연도 정수로 변환 (예: 2000년 이후 → 2000). `use_approve_date`의 연도가 이 값 이상인 매물만 남긴다.

**Step 6: 월세 상한선 (옵션)**

> "혹시 월세 상한선이 있나요?
> 이 금액을 넘는 매물은 제외하고 검색합니다.
> (예: 월세 300만원까지만 / 없으면 '없음')"

→ `max_monthly_rent_10k` 수집. "없음"이면 `null`
→ 있으면: 만원 단위로 변환 (예: 300만원 → 300)

**Step 7: 확인 및 시작**

수집한 정보를 요약하여 보여주고 확인을 받는다:

> "정리하면 이렇습니다:
> - 현재 자산: X억
> - 목표 자산: A억 (YYYY년 MM월까지)
> - 월 수익률: X%
> - 최소 목표 달성률: N% (기본 70 — 이 값 이상 매물만, 구간별 비교)
> - → 단일 시나리오 (목표 1개 × 수익률 1개)
> - 회사 이자 지원: 대출 A억까지 연 B% 지원
> - 지역: OO구, 월세
> - 희망 평수: N평 이상 ~ M평 이하 (또는 '제한 없음')
> - 사용승인일: YYYY년 이후 (또는 '제한 없음')
> - 월세 상한선: N만원 (또는 '제한 없음')
>
> 이대로 분석을 시작할까요? 수정할 부분이 있으면 말씀해주세요."

확인 후 `{RUN_DIR}/00_input/user_params.json`에 저장:

```json
{
  "total_asset_10k": 0,
  "target_asset_10k": 0,
  "target_date": "YYYY-MM",
  "monthly_rate_pct": 0,
  "min_achievement_pct": 70,
  "region": "서울 마포구",
  "housing_type": "월세",
  "min_area_sqm": null,
  "max_area_sqm": null,
  "max_monthly_rent_10k": null,
  "min_use_approve_year": null,
  "company_interest_support": {
    "available": false,
    "loan_limit_10k": 0,
    "supported_rate_pct": 0
  }
}
```

### Phase 2: 팀 구성

1. 팀 생성:
```
TeamCreate(
  team_name: "housing-advisor-team"
)
```

2. 팀원 스폰 (Agent 도구로 각각 생성):
```
Agent(
  name: "financial-planner",
  subagent_type: "financial-planner",
  model: "opus",
  team_name: "housing-advisor-team",
  prompt: "당신은 재무 시뮬레이션 전문가입니다.
    {RUN_DIR}/00_input/user_params.json을 읽고 financial-simulation 스킬을 참조하여
    단일 시나리오(목표 자산 1개 × 월 수익률 1개)에 대해 두 개의 보증금 상한선을 계산하세요:
    (1) 안전선 safe_wolse_deposit_10k = 목표 100% 정확 달성 보증금,
    (2) 공격 한계선 max_wolse_deposit_10k = user_params의 min_achievement_pct%(기본 70) 달성 보증금.
    공격 한계선이 property-researcher의 1차 필터 상한입니다. min_achievement_pct도 출력에 포함하세요.
    결과를 {RUN_DIR}/01_financial_simulation.json에 Write 도구로 새로 생성하세요.
    최신 월세 대출 금리는 WebSearch로 확인하세요.
    완료 후 리더에게 알려주세요."
)

Agent(
  name: "property-researcher",
  subagent_type: "property-researcher",
  model: "opus",
  team_name: "housing-advisor-team",
  prompt: "당신은 부동산 매물 조사 전문가입니다.
    {RUN_DIR}/00_input/user_params.json을 읽고 property-search 스킬을 참조하여
    네이버 부동산에 현재 등록된 월세 매물을 조사하세요.
    중요: 월세 데이터만 조회하세요. 매매(trades) 데이터는 조회하지 마세요.
    사용할 MCP 도구: naver_search_region으로 지역 코드를 얻고,
    naver_search_listings로 현재 매물을 수집하세요. 오피스텔/빌라 조회 금지.
    전세 매물은 제외하고 월세 매물(monthly_rent_10k > 0)만 수집하세요.
    user_params.json에 min_area_sqm/max_area_sqm이 있으면 MCP 도구 호출 시 해당 파라미터를 전달하세요.
    user_params.json에 max_monthly_rent_10k이 있으면(null이 아니면), 시나리오별 필터링 시
    monthly_rent_10k <= max_monthly_rent_10k 조건을 추가 적용하세요.
    user_params.json에 min_use_approve_year가 있으면(null이 아니면), use_approve_date의 연도가
    min_use_approve_year 이상인 매물만 남기세요 (준공 시점 필터). 수집 단계에서 바로 적용합니다.

    [중요] 다중 파일 점진적 저장 규칙:
    1. mkdir -p {RUN_DIR}/02_raw {RUN_DIR}/02_scenarios
    2. naver_search_listings 호출 후 즉시 {RUN_DIR}/02_raw/listings.json에 Write (월세만 필터링)
       — 과거 월별 조회가 아님. 현재 매물을 한 번에 수집한다.
    3. financial-planner 결과({RUN_DIR}/01_financial_simulation.json) 읽은 후,
       시나리오별로 필터링하여 즉시 {RUN_DIR}/02_scenarios/{scenario_id}.json에 Write
    4. 마지막에 {RUN_DIR}/02_property_research.json (인덱스 파일)을 Write
    각 Write의 content는 3KB(100줄) 이하로 제한하세요.

    [중요] cashflow_comment를 생성하지 마세요.
    매물의 기본 정보(단지명, 면적, 보증금, 월세, 층수, 네이버 링크)만 저장하세요.
    cashflow 계산은 strategy-reporter가 담당합니다.

    중요: 투자금이 0원이 되는(자기자본 전액을 주거에 투입하는) 방안은 제외하세요.
    해당 조건에서 매물이 없으면 '조건에 맞는 매물 없음'으로 표시하세요.
    financial-planner의 공격 한계선(max_wolse_deposit_10k, 달성률 하한 min_achievement_pct%에 해당) 이하에서
    가장 비싼(공격적인) 순으로 후보 매물을 최대 150건 'listings' 배열에 담으세요.
    달성률 정밀 필터·최대 100건 확정·구간 그룹핑은 strategy-reporter가 담당합니다.
    [중요] 여러 구를 조회할 때(예: 성남 전체 = 수정/중원/분당)는 각 구를 naver_search_region으로 따로 조회하고,
    그 구에서 수집한 매물 각각에 gu_name 필드(예: \"중원구\")를 찍어 저장하세요. 리포트 표의 매물명[구명] 표기에 쓰입니다.
    완료 후 리더에게 알려주세요."
)

Agent(
  name: "strategy-reporter",
  subagent_type: "strategy-reporter",
  model: "opus",
  team_name: "housing-advisor-team",
  prompt: "당신은 리포트 생성 전문가입니다.
    financial-planner와 property-researcher의 결과가 모두 준비되면:
    1. {RUN_DIR}/01_financial_simulation.json 읽기
    2. {RUN_DIR}/02_property_research.json (인덱스) 읽기 → 시나리오 파일 경로 확인
    3. 각 시나리오 파일({RUN_DIR}/02_scenarios/{id}.json)을 개별로 읽기
    4. strategy-report 스킬을 참조하여 각 매물별 cashflow 계산:
       - 보증금 구성 (자기자본 + 대출 내역)
       - 대출 이자 (회사 지원 반영 후 실질 월 부담액)
       - 관리비 (네이버 부동산 단지 상세에서 평형별 조회)
       - 월세 금액과 월 총 주거비 (이자+월세+관리비)
       - 남은 투자금과 예상 투자 수익
       - 목표일 예상 자산과 달성률 (달성률은 투자 자산 기준, 보증금 회수분 미반영 — 보수적)
    5. 투자금이 0원이 되는 방안은 제외하세요.
    6. [핵심] 달성률 < min_achievement_pct(기본 70) 매물은 제외하고, 통과 매물이 100건 초과 시 달성률 높은 순 상위 100건만 남기세요(잘린 건수는 주석).
    7. [핵심] 매물을 달성률 구간으로 그룹핑하세요: 🟢안전(≥100%) / 🟡절충(85~100%) / 🔴공격(70~85%). 각 구간을 별도 표(h3 class=band-{level} + report-table)로 렌더링하고, 매물명에는 [구명](gu_name)을 muted 텍스트로 병기하세요.
    8. footer에 "달성률은 투자 자산 기준이며 보증금 회수분 미반영(보수적)" 가정을 명시하세요.

    [중요] HTML 분할 생성 규칙:
    1. mkdir -p {RUN_DIR}/03_report
    2. 시나리오별로 HTML 섹션을 {RUN_DIR}/03_report/scenario_{id}.html에 개별 Write
    3. {RUN_DIR}/03_report/header.html에 DOCTYPE+CSS+사용자 조건 요약 Write
    4. {RUN_DIR}/03_report/footer.html에 면책 조항+닫기 태그 Write
    5. Bash로 cat header.html scenario_*.html footer.html > housing_report.html 조합
    각 Write의 content는 3KB(100줄) 이하로 제한하세요.
    03_strategies.json은 생성하지 마세요 (HTML에 직접 포함).

    완료 후 리더에게 파일 경로를 알려주세요."
)
```

3. 작업 등록:
```
TaskCreate([
  { title: "재무 시뮬레이션 수행", assignee: "financial-planner" },
  { title: "지역 매물 데이터 수집", assignee: "property-researcher" },
  { title: "시나리오별 매물 필터링 + 개별 파일 저장", assignee: "property-researcher", depends_on: ["재무 시뮬레이션 수행"] },
  { title: "HTML 분할 생성 + 리포트 조합", assignee: "strategy-reporter", depends_on: ["재무 시뮬레이션 수행", "시나리오별 매물 필터링 + 개별 파일 저장"] }
])
```

### Phase 3: 실행 — 팀원 자체 조율

**실행 흐름:**

```
[financial-planner]  ──────────────────────────────────────→ 완료
       │ (시뮬레이션 결과 파일 저장)
       ↓
[property-researcher] ─── 매물 수집(병렬) ──→ 필터링 ──→ 완료
       │ (매물 데이터 파일 저장)
       ↓
[strategy-reporter]  ─── 전략 도출 ──→ HTML 생성 ──→ 완료
```

**팀원 간 통신 규칙:**
- financial-planner는 시뮬레이션 완료 시 property-researcher에게 SendMessage로 알림
- property-researcher는 매물 조사 완료 시 strategy-reporter에게 SendMessage로 알림
- 각 팀원은 결과를 파일로 저장하고 리더에게 완료 알림

**산출물 저장:**

| 팀원 | 출력 경로 |
|------|----------|
| financial-planner | `{RUN_DIR}/01_financial_simulation.json` |
| property-researcher | `{RUN_DIR}/02_raw/listings.json` + `{RUN_DIR}/02_scenarios/*.json` + `{RUN_DIR}/02_property_research.json` (인덱스) |
| strategy-reporter | `{RUN_DIR}/03_report/*.html` + `{RUN_DIR}/housing_report.html` (Bash cat 조합) |

**리더 모니터링:**
- 팀원 유휴 알림 수신 시 진행 상황 확인
- 특정 팀원이 막혔을 때 SendMessage로 지시
- 전체 진행률은 TaskGet으로 확인

### Phase 4: 결과 검증 및 전달

1. 모든 팀원 작업 완료 대기
2. 산출물 존재 확인:
   - `{RUN_DIR}/02_raw/listings.json` 매물 파일 존재 확인
   - `{RUN_DIR}/02_scenarios/` 디렉토리에 시나리오별 파일 존재 확인
   - `{RUN_DIR}/02_property_research.json` 인덱스 파일 존재 확인
   - `{RUN_DIR}/03_report/` 디렉토리에 HTML 파트 파일 존재 확인
   - `{RUN_DIR}/housing_report.html` 최종 리포트 존재 + 크기 > 0 확인
3. 리포트 내용 간략 검증:
   - 달성률 구간별 매물(최대 100건, 안전/절충/공격)이 포함되었는지
   - 각 매물에 예상 자산 달성률·구 이름(매물명[구명])이 표시되었는지
   - 달성률 < min_achievement_pct 매물이 표에 섞이지 않았는지
   - 금액 계산에 명백한 오류가 없는지
4. 사용자에게 결과 요약 보고:
   - 달성률 구간별 매물(최대 100건) 한줄 요약
   - `{RUN_DIR}/housing_report.html` 파일 경로
5. 리포트를 크롬 브라우저로 자동 열기:
   ```bash
   open -a "Google Chrome" {RUN_DIR}/housing_report.html
   ```

### Phase 5: 정리

1. 팀원들에게 종료 요청 (SendMessage)
2. 팀 정리 (TeamDelete)
3. `_workspace/` 디렉토리 보존 (중간 산출물 감사 추적용)
4. 사용자에게 최종 안내

## 데이터 흐름

```
[사용자 입력]
     ↓
[리더: {RUN_DIR}/00_input/user_params.json 저장]
     ↓
[financial-planner] → {RUN_DIR}/01_financial_simulation.json
     ↓ (SendMessage: 시뮬레이션 완료)
[property-researcher] → {RUN_DIR}/02_raw/listings.json + {RUN_DIR}/02_scenarios/*.json + {RUN_DIR}/02_property_research.json (인덱스)
     ↓ (SendMessage: 매물 조사 완료)
[strategy-reporter] → {RUN_DIR}/03_report/*.html → Bash cat → {RUN_DIR}/housing_report.html
     ↓
[리더: 검증 + 사용자 전달]
```

## 에러 핸들링

| 상황 | 전략 |
|------|------|
| MCP 서버 연결 실패 | 네이버 부동산 API 접속 상태 확인 (HTTP 403/429 등) |
| financial-planner 실패 | 1회 재시도. 재실패 시 기본 대출 금리(연 4%)로 수동 계산 |
| property-researcher 실패 | 1회 재시도. 재실패 시 매물 없이 시뮬레이션 결과만으로 리포트 생성 |
| strategy-reporter 실패 | 1회 재시도. 재실패 시 리더가 직접 간이 리포트 생성 |
| 매물 0건 | 인접 지역 확대 또는 조건 완화 제안 후 재조사 |
| 팀원 과반 실패 | 사용자에게 알리고 진행 여부 확인 |
| 데이터 충돌 | 출처 명시 후 병기, 삭제하지 않음 |

## 테스트 시나리오

### 정상 흐름
1. 사용자가 "현재 자산 3억, 목표 5억, 2년 후, 월 수익률 1%, 서울 마포구" 입력
2. Phase 1에서 user_params.json 저장
3. Phase 2에서 팀 구성 (3명 + 4개 작업)
4. Phase 3에서:
   - financial-planner가 단일 시나리오 시뮬레이션 완료
   - property-researcher가 마포구 현재 매물 수집 → 02_raw/listings.json + 02_scenarios/*.json + 인덱스 저장
   - strategy-reporter가 시나리오 파일 읽기 → cashflow 계산 → HTML 분할 생성 → cat 조합
5. Phase 4에서 02_raw/listings.json, 02_scenarios/, 03_report/ 디렉토리 + housing_report.html 검증 후 사용자에게 전달
6. 예상 결과: `housing_report.html` 생성, 달성률 구간별 매물(최대 100건) 비교표 포함

### 에러 흐름
1. Phase 3에서 property-researcher가 MCP 호출 실패
2. 리더가 유휴 알림 수신
3. SendMessage로 상태 확인 → 재시도 지시
4. 재시도 실패 시 매물 데이터 없이 진행
5. strategy-reporter가 시뮬레이션 결과만으로 리포트 생성
6. 최종 리포트에 "매물 데이터 미수집 — 직접 부동산 앱에서 확인 필요" 명시
