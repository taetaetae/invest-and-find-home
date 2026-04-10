# invest-and-find-home

자산 증식 목표를 유지하면서 가장 공격적인(비싼) 월세 매물을 추천하는 AI 에이전트 팀 기반 주거 전략 어드바이저.

## 개요

"투자와 주거, 두 마리 토끼를 잡자"가 핵심 컨셉입니다.

사용자의 현재 자산, 목표 자산, 투자 수익률, 회사 이자 지원 조건을 입력받아 **9가지 시나리오**(목표 자산 3가지 × 월 수익률 3가지)를 시뮬레이션하고, 각 시나리오에서 목표 달성이 가능한 범위 내 월세 매물 TOP 10을 HTML 리포트로 제공합니다.

## 아키텍처

```
[사용자 입력] → [housing-advisor 오케스트레이터]
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
 financial-planner  property-researcher  strategy-reporter
 (재무 시뮬레이션)    (매물 조사)          (HTML 리포트)
        │               │               │
        ▼               ▼               ▼
 01_financial_     02_property_      housing_report.html
 simulation.json   research.json
```

### 에이전트 팀

| 에이전트 | 역할 | 스킬 |
|---------|------|------|
| financial-planner | 9가지 시나리오별 재무 시뮬레이션, 최대 월세 가능 금액 산출 | financial-simulation |
| property-researcher | 지역별 월세 매물 수집 및 시나리오별 TOP 10 선별 | property-search |
| strategy-reporter | 재무 + 매물 데이터를 종합하여 HTML 비교 리포트 생성 | strategy-report |

### MCP 서버

`mcp-servers/real-estate-mcp/` — 국토교통부 공공데이터 API 기반 부동산 실거래가 MCP 서버

- 아파트 / 오피스텔 / 빌라 / 단독주택 매매·전월세 조회
- 청약 공고·결과 조회
- 온비드 공매 조회
- 복리 계산, 대출 상환, 월 현금흐름 계산

## 사전 준비

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (Python 패키지 매니저)
- [direnv](https://direnv.net/) (환경변수 자동 로드)
- [공공데이터포털](https://www.data.go.kr) API 키 — 필요한 서비스 목록은 `mcp-servers/real-estate-mcp/README-ko.md` 참조

## 설치

```bash
git clone --recurse-submodules <repository_url>
cd invest-and-find-home
```

`.envrc` 파일에 API 키를 설정합니다:

```bash
export DATA_GO_KR_API_KEY="your_api_key_here"
```

direnv를 허용합니다:

```bash
direnv allow
```

## 사용법

Claude Code에서 `시작하자` 또는 `시작`을 입력하면 housing-advisor 스킬이 트리거됩니다.

### 입력 항목

1. **현재 자산과 목표** — 총 자산, 목표 자산 3가지, 달성 시점
2. **월 수익률** — 3가지 가정 (예: 월 1%, 3%, 5%)
3. **회사 이자 지원** — 대출 한도, 지원 이자율 (없으면 '없음')
4. **희망 지역과 평수** — 지역명, 평수 범위

### 산출물

매 실행마다 `_workspace/YYYY-MM-DD_HHmm/` 디렉토리가 생성됩니다:

```
_workspace/2026-04-10_0132/
├── 00_input/
│   └── user_params.json           # 사용자 입력 파라미터
├── 01_financial_simulation.json   # 재무 시뮬레이션 결과
├── 02_property_research.json      # 매물 조사 결과
└── housing_report.html            # 최종 HTML 리포트
```

`housing_report.html`을 브라우저에서 열면 시나리오별 월세 TOP 10 비교 리포트를 확인할 수 있습니다.

## 프로젝트 구조

```
invest-and-find-home/
├── .claude/
│   ├── agents/                    # 에이전트 정의
│   │   ├── financial-planner.md
│   │   ├── property-researcher.md
│   │   └── strategy-reporter.md
│   └── skills/                    # 스킬 정의
│       ├── housing-advisor/       # 오케스트레이터 스킬
│       ├── financial-simulation/  # 재무 시뮬레이션 스킬
│       ├── property-search/       # 매물 검색 스킬
│       └── strategy-report/       # 리포트 생성 스킬
├── mcp-servers/
│   └── real-estate-mcp/           # 부동산 데이터 MCP 서버
├── _workspace/                    # 실행 결과 (타임스탬프별)
├── .mcp.json                      # MCP 서버 설정
└── .envrc                         # 환경변수 설정
```

## 라이선스

이 프로젝트의 MCP 서버(`mcp-servers/real-estate-mcp/`)는 MIT 라이선스를 따릅니다.
