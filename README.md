# invest-and-find-home

자산 증식 목표를 유지하면서 가장 공격적인(비싼) 월세 매물을 추천하는 AI 에이전트 팀 기반 주거 전략 어드바이저.

## 개요

"투자와 주거, 두 마리 토끼를 잡자"가 핵심 컨셉입니다.

사용자의 현재 자산, 목표 자산, 투자 수익률, 회사 이자 지원 조건을 입력받아 **9가지 시나리오**(목표 자산 3가지 × 월 수익률 3가지)를 시뮬레이션하고, **네이버 부동산의 현재 등록 매물** 중 각 시나리오에서 목표 달성이 가능한 범위 내 월세 매물 TOP 10을 HTML 리포트로 제공합니다.

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
 simulation.json   research.json     → 크롬 자동 열기
```

### 에이전트 팀

| 에이전트 | 역할 | 스킬 |
|---------|------|------|
| financial-planner | 9가지 시나리오별 재무 시뮬레이션, 최대 월세 가능 금액 산출 | financial-simulation |
| property-researcher | 네이버 부동산 현재 매물 수집 및 시나리오별 TOP 10 선별 | property-search |
| strategy-reporter | 재무 + 매물 데이터를 종합하여 HTML 비교 리포트 생성 | strategy-report |

### MCP 서버

`mcp-servers/naver-land-mcp/` — 네이버 부동산 현재 매물 기반 MCP 서버

- 네이버 부동산(new.land.naver.com) 현재 등록 매물 조회
- 지역/동/단지 목록 조회
- 단지별 매물 목록 (보증금, 월세, 면적, 층수, 네이버 링크 포함)
- 복리 계산, 대출 상환, 월 현금흐름 계산

기술 스택: Python + curl_cffi (Chrome TLS 핑거프린트) + Playwright (JWT 토큰 자동 획득)

## 사전 준비

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (Python 패키지 매니저)
- Chromium 브라우저 (Playwright가 자동 설치)

## 설치

```bash
git clone <repository_url>
cd invest-and-find-home
cd mcp-servers/naver-land-mcp && uv sync && uv run playwright install chromium && cd ../..
```

API 키 설정이 필요 없습니다. 네이버 부동산은 공개 API를 사용합니다.

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
_workspace/2026-04-11_0030/
├── 00_input/
│   └── user_params.json           # 사용자 입력 파라미터
├── 01_financial_simulation.json   # 재무 시뮬레이션 결과
├── 02_raw/
│   └── listings.json              # 네이버 부동산 현재 매물
├── 02_scenarios/                  # 시나리오별 TOP 10 매물
│   ├── 목표12억_수익률1%.json
│   ├── 목표12억_수익률2%.json
│   └── ...
├── 02_property_research.json      # 매물 조사 인덱스
├── 03_report/                     # HTML 파트 파일
│   ├── header.html
│   ├── scenario_*.html
│   └── footer.html
└── housing_report.html            # 최종 HTML 리포트 → 크롬 자동 열기
```

`housing_report.html`은 리포트 생성 완료 시 크롬 브라우저에서 자동으로 열립니다.

### 리포트 기능

- 시나리오별 월세 TOP 10 비교 테이블
- 매물명 클릭 시 네이버 부동산 매물 페이지로 이동
- 동/향/등록일/사용승인일 별도 열로 표시
- 테이블 헤더 클릭으로 열별 정렬 (면적, 보증금, 달성률 등)
- 면적 내림차순 기본 정렬

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
│   └── naver-land-mcp/            # 네이버 부동산 MCP 서버
├── _workspace/                    # 실행 결과 (타임스탬프별)
└── .mcp.json                      # MCP 서버 설정
```

## 샘플 결과물

![샘플 리포트](sample.png)

## 라이선스

MIT
