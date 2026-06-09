---
name: strategy-report
description: "부동산 월세 전략 리포트 생성. 재무 시뮬레이션과 매물 데이터를 종합하여 단일 시나리오(목표 자산 1개 × 월 수익률 1개)의 월세 매물을 달성률 구간별로 최대 100건까지 HTML 리포트로 작성. 주거 전략, 대출 전략, 투자 전략표, 자산 변화 그래프 포함. 부동산 리포트, 주거 전략 리포트 요청 시 반드시 이 스킬을 사용할 것."
---

# Strategy Report

재무 시뮬레이션의 단일 시나리오(목표 자산 1개 × 월 수익률 1개)에서, 사용자가 감수하는 최소 달성률(`min_achievement_pct`, 기본 70%)부터 100%+까지의 월세 매물을 **달성률 구간별로 최대 100건** 추천하는 HTML 리포트를 생성하는 스킬. 더 비싼 집(달성률 낮음)과 안전한 선택(달성률 높음)의 트레이드오프를 한눈에 비교할 수 있게 구성한다.

## 리포트 원칙

### 0. 헤더: 조회 기준 + 재무 조건 명시 (필수)

리포트 상단 헤더에 **"어떤 기준으로 매물을 조회했는지"** 를 반드시 명시한다. 헤더는 두 블록으로 구성한다.

**1-A. 조회 기준 (매물 검색 조건)** — 매물 필터 조건을 그대로 노출한다:

| 항목 | 값 | 출처 |
|------|-----|------|
| 조회 지역 | 분당구, 서초구, … | `02_property_research.json`의 `region.name` (없으면 `00_input/user_params.json`의 `region`) |
| 주거 유형 | 아파트 월세 (고정) | — |
| 평수 범위 | 25~35평 (82.6~115.7㎡) | `user_params.json`의 `min_area_sqm`/`max_area_sqm`. ㎡→평 = ÷3.3058. 미지정 시 "제한 없음" |
| 사용승인일 | 2000년 이후 | `user_params.json`의 `min_use_approve_year`. **`null`이면 "제한 없음"** 으로 표기 |
| 월세 상한 | 150만원 | `user_params.json`의 `max_monthly_rent_10k`(만원). **`null`이면 "제한 없음"** 으로 표기 |

- **월세 상한은 매물 결과를 좌우하는 핵심 필터이므로 헤더에 반드시 노출**하고 `.highlight` 클래스로 강조한다.
- 평수/사용승인일/월세 상한이 미지정(`null`)이면 해당 cond-value를 **"제한 없음"** 으로 출력한다.

**1-B. 재무 조건 (자산 시뮬레이션 입력)**: 총자산 / 목표자산 / 월수익률 / 투자기간 / 대출한도 / 실질 대출금리.

두 블록은 각각 `.cond-group-label`(📍 조회 기준 / 💰 재무 조건) 소제목으로 구분한다.

### 1. 구성: 달성률 구간별 매물 (최대 100건)

property-researcher가 넘긴 후보 매물(`listings`)에 대해 매물별 cashflow·달성률을 계산한 뒤, 다음 순서로 최종 매물을 확정한다.

1. **달성률 하한 필터**: 매물별 달성률이 `min_achievement_pct`(기본 70) 미만이면 제외. 투자금이 0원이 되는 방안도 제외.
2. **최대 100건 컷**: 통과 매물이 100건을 초과하면 **달성률 높은 순으로 상위 100건**만 남긴다. 잘린 매물 수(주로 공격 구간)는 리포트에 주석으로 명시한다(예: "공격 구간 12건이 100건 초과로 미표시").
3. **달성률 구간(밴드) 그룹핑** — 표를 3개 묶음으로 분리해 트레이드오프를 한눈에 보이게 한다:

   | 구간 | 달성률 | 색(클래스) | 의미 |
   |------|--------|-----------|------|
   | 🟢 안전 | ≥ 100% | safe | 목표 달성/초과 |
   | 🟡 절충 | 85% ~ 100% | warn | 목표에 거의 근접 |
   | 🔴 공격 | 70% ~ 85% | danger | 목표 미달 감수, 더 비싼 집 |

   - 구간 경계는 `min_achievement_pct`가 70일 때 기준이다. 하한은 항상 `min_achievement_pct`와 같다(예: 60이면 공격 구간이 60~85%로 넓어짐).
   - 각 구간 안에서는 면적 내림차순(동일 면적이면 보증금 내림차순)으로 정렬하고, 헤더 클릭으로 재정렬할 수 있다(인터랙티브 정렬).
   - 빈 구간은 "해당 매물 없음"으로 표기하거나 생략한다.

### 2. 각 매물에 포함할 정보

```
- 매물명 (네이버 부동산 링크), 층수, 면적(평수)
- 등록일, 사용승인일 (단지 준공 시점)
- 월세: 보증금 / 월세
- 관리비 (월)
- 보증금 구성: 자기자본 + 대출 내역
- 대출 월이자 (회사 지원 반영 후 실질 부담액)
- 월 총 주거비 (대출이자 + 월세 + 관리비)
- 남은 투자금
- 목표일 예상 자산 (복리 계산)
- 목표 달성률 (%)
```

cashflow 계산 공식:
```
대출_금액 = min(보증금, 대출한도)
자기자본_투입 = 보증금 - 대출_금액
남은_투자금 = 총자산 - 자기자본_투입
대출_월이자 = 대출_금액 × max(0, 대출금리 - 회사지원금리) / 100 / 12
월_총_주거비 = 대출_월이자 + 월세 + 관리비
목표일_예상자산 = 남은_투자금 × (1 + 월수익률/100)^남은개월수 (매월 주거비 차감 복리)
달성률 = 목표일_예상자산 / 목표자산 × 100
```

**달성률 모델 주의(보수적 가정)**: `예상자산`은 **투자 자산만** 추적한다. 보증금에 넣은 자기자본(`자기자본_투입`)은 주거에 묶여 운용 못 하는 기회비용으로 보고, 임대 종료 시 돌려받는 보증금 회수분은 예상자산에 **더하지 않는다**. 따라서 보증금이 클수록 달성률이 뚜렷이 떨어진다(이 민감도가 70~100% 트레이드오프 스펙트럼을 만든다). 실제 순자산은 보증금만큼 더 많으므로 보수적 추정이며, 리포트 footer에 이 가정을 명시한다.

**달성률 하한 필터 + 최대 100건**:
- 달성률 < `min_achievement_pct`(기본 70) 매물은 제외한다. 투자금 0원 방안도 제외한다.
- 통과 매물이 100건 초과 시 **달성률 높은 순 상위 100건**만 남기고, 잘린 건수를 주석으로 명시한다.

관리비 참고:
- `maintenance_fee_10k` — 네이버 부동산 단지 상세에서 평형별 연평균 관리비를 조회한다
- 관리비가 0이면 리포트에 "-" 로 표시한다
- 관리비는 매물별로 다르므로 시나리오 매트릭스에는 포함하지 않고 "관리비 별도" 주석을 표시한다

### 3. 매물 배열 규칙

- **달성률 구간(밴드)별로 3개 묶음으로 분리**: 🟢 안전(≥100%) / 🟡 절충(85~100%) / 🔴 공격(70~85%). 각 묶음은 별도의 `.report-table`로 렌더링한다.
- 각 구간 내 기본 정렬: 면적 내림차순 (동일 면적이면 보증금 내림차순, 동일 보증금이면 월세 오름차순). 헤더 클릭으로 재정렬 가능(인터랙티브 정렬).
- 매물명은 `매물명[구명]` 형식으로 구를 병기한다(`gu_name`).

## HTML 리포트 구조

아래 참조 템플릿의 구조와 CSS를 그대로 따른다. 데이터만 실제 값으로 교체한다.

### 참조 HTML 템플릿

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>주거 전략 리포트 — {지역명}</title>
<!-- 지도(Leaflet): 지도 섹션 전용 외부 의존. 오프라인이면 타일만 미표시되고 표·마커 데이터는 영향 없음 -->
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin=""/>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,'Noto Sans KR',sans-serif;background:#f5f5f5;color:#333;min-width:1280px;line-height:1.6}
.container{max-width:1400px;margin:0 auto;padding:20px}
header{background:linear-gradient(135deg,#1a237e,#283593);color:#fff;padding:32px;border-radius:12px;margin-bottom:24px}
header h1{font-size:24px;margin-bottom:12px}
.conditions{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin-top:16px}
.cond-item{background:rgba(255,255,255,0.12);padding:10px 14px;border-radius:8px;font-size:14px}
.cond-label{font-size:11px;opacity:0.7;margin-bottom:2px}
.cond-value{font-size:16px;font-weight:600}
.cond-group-label{font-size:13px;font-weight:700;opacity:0.9;margin-top:18px;margin-bottom:8px;letter-spacing:0.3px;border-left:3px solid rgba(255,255,255,0.5);padding-left:8px}
.cond-item.highlight{background:rgba(255,235,59,0.2);border:1px solid rgba(255,235,59,0.5)}
.matrix{background:#fff;border-radius:12px;padding:24px;margin-bottom:24px;box-shadow:0 2px 8px rgba(0,0,0,0.06)}
.matrix h2{font-size:18px;margin-bottom:16px;color:#1a237e}
.matrix table{width:100%;border-collapse:collapse;font-size:14px}
.matrix th,.matrix td{padding:10px 12px;text-align:center;border:1px solid #e0e0e0}
.matrix th{background:#f5f5f5;font-weight:600}
.matrix .safe{background:#e8f5e9;color:#2e7d32}
.matrix .warn{background:#fff3e0;color:#e65100}
.matrix .danger{background:#ffebee;color:#c62828}
.scenario-section{background:#fff;border-radius:12px;padding:24px;margin-bottom:24px;box-shadow:0 2px 8px rgba(0,0,0,0.06)}
.scenario-section h2{font-size:18px;margin-bottom:4px;color:#1a237e}
.scenario-meta{font-size:13px;color:#666;margin-bottom:16px}
.report-container{overflow-x:auto}
.report-table{min-width:1300px;width:100%;border-collapse:collapse;font-size:13px}
.report-table th{background:#f5f5f5;padding:10px 8px;text-align:center;border:1px solid #e0e0e0;font-weight:600;white-space:nowrap;cursor:pointer;user-select:none}
.report-table td{padding:8px;text-align:center;border:1px solid #e0e0e0;white-space:nowrap}
.report-table tbody tr:hover{background:#f0f4ff}
.report-table .name-cell{text-align:left;max-width:240px;overflow:hidden;text-overflow:ellipsis}
.report-table a{color:#1565c0;text-decoration:none}
.report-table a:hover{text-decoration:underline}
.band-safe{color:#2e7d32}
.band-warn{color:#e65100}
.band-danger{color:#c62828}
.badge-safe{display:inline-block;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600;background:#e8f5e9;color:#2e7d32}
.badge-warn{display:inline-block;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600;background:#fff3e0;color:#e65100}
.badge-danger{display:inline-block;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600;background:#ffebee;color:#c62828}
.bar-container{width:100%;background:#e0e0e0;border-radius:4px;height:18px;position:relative;min-width:80px}
.bar-fill{height:100%;border-radius:4px;display:flex;align-items:center;justify-content:flex-end;padding-right:4px;font-size:10px;font-weight:600;color:#fff;min-width:30px}
.bar-safe{background:linear-gradient(90deg,#66bb6a,#43a047)}
.bar-warn{background:linear-gradient(90deg,#ffa726,#fb8c00)}
.bar-danger{background:linear-gradient(90deg,#ef5350,#e53935)}
.loan-summary{background:#fff;border-radius:12px;padding:24px;margin-bottom:24px;box-shadow:0 2px 8px rgba(0,0,0,0.06)}
.loan-summary h2{font-size:18px;margin-bottom:12px;color:#1a237e}
.loan-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:16px}
.loan-card{background:#f8f9fa;padding:16px;border-radius:8px;border-left:4px solid #1a237e}
.loan-card .label{font-size:12px;color:#666}
.loan-card .value{font-size:18px;font-weight:700;color:#1a237e}
footer{text-align:center;padding:24px;color:#999;font-size:12px;line-height:1.8}
/* 지도 섹션 (표 아래 통합 지도) */
.map-section{background:#fff;border-radius:12px;padding:24px;margin-bottom:24px;box-shadow:0 2px 8px rgba(0,0,0,0.06)}
.map-section h2{font-size:18px;margin-bottom:4px;color:#1a237e}
.map-meta{font-size:13px;color:#666;margin-bottom:12px}
#map{width:100%;height:560px;border-radius:8px;border:1px solid #e0e0e0;z-index:0}
.map-note{font-size:12px;color:#888;margin-top:8px}
/* 가격표 핀 (Leaflet divIcon) — 좌표에 tip 정렬 */
.price-pin{position:absolute;transform:translate(-50%,-100%);cursor:pointer}
.price-pin .pin-body{background:#fff;border:2px solid var(--pin-color,#1a237e);border-radius:8px;padding:3px 8px;box-shadow:0 2px 6px rgba(0,0,0,0.25);white-space:nowrap;text-align:center}
.price-pin .pin-rent{font-weight:700;font-size:12px;color:#1a237e}
.price-pin .pin-sub{font-size:10px;color:var(--pin-color,#1a237e);font-weight:600}
.price-pin .pin-tail{position:absolute;left:50%;bottom:-7px;transform:translateX(-50%);width:0;height:0;border-left:6px solid transparent;border-right:6px solid transparent;border-top:7px solid var(--pin-color,#1a237e)}
.pin-popup{font-size:12px;max-height:240px;overflow:auto}
.pin-popup h3{font-size:13px;margin-bottom:6px;color:#1a237e}
.pin-popup table{border-collapse:collapse;width:100%}
.pin-popup th,.pin-popup td{border:1px solid #e0e0e0;padding:3px 5px;text-align:center;white-space:nowrap}
.pin-popup a{color:#1565c0;text-decoration:none}
</style>
</head>
<body>
<div class="container">

<!-- 1. 헤더: 제목 + 생성일자 + [조회 기준] + [재무 조건] -->
<header>
<h1>주거 전략 리포트 — {지역명} 아파트 월세</h1>
<p style="opacity:0.8;font-size:14px">데이터 기준일: {YYYY-MM-DD}</p>

<!-- 1-A. 조회 기준 (매물 검색 조건) — 어떤 기준으로 매물을 조회했는지 명시 -->
<div class="cond-group-label">📍 조회 기준 (매물 검색 조건)</div>
<div class="conditions">
<div class="cond-item"><div class="cond-label">조회 지역</div><div class="cond-value">{지역명}</div></div>
<div class="cond-item"><div class="cond-label">주거 유형</div><div class="cond-value">아파트 월세</div></div>
<div class="cond-item"><div class="cond-label">평수 범위</div><div class="cond-value">{평수범위} ({㎡범위})</div></div>
<div class="cond-item"><div class="cond-label">사용승인일</div><div class="cond-value">{사용승인조건}</div></div>
<div class="cond-item highlight"><div class="cond-label">월세 상한</div><div class="cond-value">{월세상한}</div></div>
</div>

<!-- 1-B. 재무 조건 (시뮬레이션 입력) -->
<div class="cond-group-label">💰 재무 조건 (자산 시뮬레이션)</div>
<div class="conditions">
<div class="cond-item"><div class="cond-label">총 자산</div><div class="cond-value">{총자산}</div></div>
<div class="cond-item"><div class="cond-label">목표 자산</div><div class="cond-value">{목표}억</div></div>
<div class="cond-item"><div class="cond-label">월 수익률</div><div class="cond-value">{수익률}%</div></div>
<div class="cond-item"><div class="cond-label">투자 기간</div><div class="cond-value">{N}개월 ({시작}~{종료})</div></div>
<div class="cond-item"><div class="cond-label">대출 한도</div><div class="cond-value">{대출한도}</div></div>
<div class="cond-item"><div class="cond-label">실질 대출금리</div><div class="cond-value">연 {실질금리}% (회사지원 반영)</div></div>
</div>
</header>

<!-- 2. 전략 요약: 단일 시나리오 -->
<div class="matrix">
<h2>전략 요약 — 목표 {목표}억 / 월 수익률 {수익률}%</h2>
<table>
<thead>
<tr><th>달성 가능</th><th>최대 보증금</th><th>최대 월세 / 월 주거비</th><th>필요 투자금</th></tr>
</thead>
<tbody>
<!-- 단일 행에 class="safe|warn|danger" 적용 -->
<tr class="{level}"><td>{가능여부}</td><td>{보증금}</td><td>월세 {월세} + 이자 {이자}<br>= 월 주거비 {월주거비}</td><td>{필요투자금}</td></tr>
</tbody>
</table>
<p style="font-size:12px;color:#888;margin-top:8px">* 보증금 = 최대 가능 보증금, 월세 = 최대 가능 월세 (대출이자 차감 후) / 관리비 별도 (매물별 상이)</p>
</div>

<!-- 3. 대출 조건 요약 카드 -->
<div class="loan-summary">
<h2>대출 조건 요약</h2>
<div class="loan-grid">
<div class="loan-card"><div class="label">대출 합계</div><div class="value">{대출합계}</div><div class="label">{대출상세}</div></div>
<div class="loan-card"><div class="label">월 이자 합계</div><div class="value">{월이자합계}</div><div class="label">{이자상세}</div></div>
<div class="loan-card"><div class="label">상환 방식</div><div class="value">거치식</div><div class="label">원금 만기일시상환, 이자만 납부</div></div>
</div>
</div>

<!-- 4. 매물 — 달성률 구간별 (단일 시나리오, 최대 100건) -->
<div class="scenario-section">
<h2>시나리오: 목표 {목표}억 / 월 수익률 {수익률}% — 매물 {N}건 (최대 100)</h2>
<div class="scenario-meta">안전선 보증금(100%): {안전선보증금} | 공격 한계선(달성률 {최소달성률}%): {공격한계보증금} | 최대 월세: {월세}{컷주석}</div>
<!-- {컷주석} 예: " | ⚠ 공격 구간 12건이 100건 초과로 미표시" (잘린 매물 없으면 "") -->

<!-- ▼ 아래 [h3 + report-container>table] 블록을 달성률 구간 3개에 대해 반복한다.
     안전(🟢 ≥100% safe) → 절충(🟡 85~100% warn) → 공격(🔴 70~85% danger) 순.
     {level}=safe|warn|danger, {구간이모지}=🟢|🟡|🔴, {구간명}=안전|절충|공격, {구간범위}=달성률 표기, {구간건수}=그 구간 매물 수.
     빈 구간은 <h3> 아래에 "<p style=\"color:#888;font-size:13px\">해당 매물 없음</p>"으로 표기하거나 블록 자체를 생략한다. -->
<h3 class="band-{level}" style="margin:18px 0 8px;font-size:15px">{구간이모지} {구간명} — {구간범위} <span style="color:#888;font-weight:400">({구간건수}건)</span></h3>
<div class="report-container">
<table class="report-table">
<thead><tr>
<th data-sort-type="number">#</th>
<th data-sort-type="text">매물명</th>
<th data-sort-type="text">층</th>
<th data-sort-type="number">면적(평)</th>
<th data-sort-type="text">등록일</th>
<th data-sort-type="text">사용승인일</th>
<th data-sort-type="text">보증금/월세</th>
<th data-sort-type="number">관리비</th>
<th data-sort-type="text">보증금 구성</th>
<th data-sort-type="number">대출이자(월)</th>
<th data-sort-type="number">월 주거비</th>
<th data-sort-type="number">투자가능금</th>
<th data-sort-type="number">예상자산</th>
<th data-sort-type="number">달성률</th>
</tr></thead>
<tbody>
<tr>
<td>1</td>
<td class="name-cell"><a href="{article_url}" target="_blank">{매물명}</a><span style="color:#888;font-size:11px"> [{구명}]</span></td>
<td>{층}</td>
<td>{면적}</td>
<td>{등록일}</td>
<td>{사용승인일}</td>
<td>{보증금}/{월세}</td>
<td>{관리비}만</td>
<td>대출 {대출액}<br>자기자본 {자기자본}</td>
<td>{대출이자}만</td>
<td>{월주거비}만</td>
<td>{투자금}</td>
<td><div class="bar-container"><div class="bar-fill bar-{level}" style="width:{pct}%">{예상자산}</div></div></td>
<td><span class="badge-{level}">{달성률}%</span></td>
</tr>
<!-- ... 그 구간 내 매물 반복 (면적 내림차순) -->
</tbody>
</table>
</div>
<!-- ▲ 위 블록을 안전/절충/공격 3개 구간에 대해 반복 -->
</div>
<!-- 단일 시나리오 (반복 없음) -->

<!-- 4-B. 매물 지도 (표 아래 통합 지도) — map.html 로 분할 생성 -->
<div class="map-section">
<h2>매물 지도 — 단지별 위치</h2>
<div class="map-meta">마커 = 단지(같은 단지 매물은 하나로 묶음) · 색 = 목표 달성률(safe/warn/danger) · 클릭 시 단지 매물 목록</div>
<div id="map"></div>
<p class="map-note">{지도주석}</p><!-- 예: "지도 미표시 단지 3개 (좌표 미확보) — 위 표에는 포함됨". 미표시 0건이면 생략 또는 "" -->
</div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>
<script>
// 단지별 마커 데이터 — strategy-reporter가 최종 확정 매물(최대 100건)을 complex_no로 집계해 채운다.
// 한 단지 = 한 객체. lat/lng 없으면(null) 지도에서 제외(표에는 유지). minRent=단지 내 최저 월세(만원).
// level=그 단지 최고 달성률 기준 safe/warn/danger. count=단지 내 매칭 매물 수.
// ⚠ 반드시 "유효한 JSON 리터럴"로 작성한다: 모든 문자열은 큰따옴표(")로 감싸고 내부 " 와 \ 만 escape.
//   (JSON은 JS의 부분집합이라 그대로 동작) 작은따옴표 문자열로 직렬화하지 말 것 — 단지명에 ' 가 있으면 깨진다.
var COMPLEXES = [
  // {"name":"래미안 마포리버뷰","lat":37.5421,"lng":126.9389,"households":1234,"count":3,"minRent":160,"level":"safe",
  //  "listings":[{"floor":"19/25","pyeong":25.7,"deposit":"2억","rent":160,"fee":41,"rate":104,"url":"https://..."}]}
];
(function(){
  var el = document.getElementById('map');
  if (!el) return;
  function esc(s){ return String(s==null?'':s).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];}); }
  function safeUrl(u){ u=String(u==null?'':u); return /^https?:\/\//i.test(u)?u:'#'; }  // javascript: 등 스킴 차단
  var withGeo = COMPLEXES.filter(function(c){ return c.lat!=null && c.lng!=null; });
  if (!withGeo.length) {  // 좌표 있는 단지 0건 — 지도 생성 자체를 생략(center 미설정 빈 박스 방지)
    el.innerHTML = '<div style="padding:40px;text-align:center;color:#888">표시할 좌표가 있는 단지가 없습니다. (매물 표는 위에 표시됩니다)</div>';
    return;
  }
  if (typeof L === 'undefined') {  // Leaflet 로드 실패(오프라인 등) — 타일만 미표시, 표는 영향 없음
    el.innerHTML = '<div style="padding:40px;text-align:center;color:#888">지도를 불러오지 못했습니다. 인터넷 연결 후 새로고침하세요. (매물 표는 위에 그대로 표시됩니다)</div>';
    return;
  }
  function popupHtml(c){
    var rows=(c.listings||[]).map(function(l){
      return '<tr><td>'+esc(l.floor)+'</td><td>'+esc(l.pyeong)+'평</td>'
        +'<td>'+esc(l.deposit)+' / 월'+esc(l.rent)+'만</td>'
        +'<td>'+(l.fee?esc(l.fee)+'만':'-')+'</td><td>'+(l.rate!=null?esc(l.rate):'-')+'%</td>'
        +'<td><a href="'+esc(safeUrl(l.url))+'" target="_blank" rel="noopener">보기</a></td></tr>';
    }).join('');
    return '<div class="pin-popup"><h3>'+esc(c.name)+(c.households?' · '+esc(c.households)+'세대':'')+'</h3>'
      +'<table><thead><tr><th>층</th><th>면적</th><th>보증/월세</th><th>관리비</th><th>달성률</th><th>링크</th></tr></thead>'
      +'<tbody>'+rows+'</tbody></table></div>';
  }
  var COLORS={safe:'#43a047',warn:'#fb8c00',danger:'#e53935'}, pts=[];
  var map=L.map('map');
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'© OpenStreetMap contributors'}).addTo(map);
  withGeo.forEach(function(c){
    var color=COLORS[c.level]||'#1a237e';
    var rentLabel=(c.minRent!=null&&c.minRent>0)?esc(c.minRent):'-';
    var html='<div class="price-pin" style="--pin-color:'+color+'">'
      +'<div class="pin-body"><div class="pin-rent">월'+rentLabel+'만</div>'
      +'<div class="pin-sub">'+esc(c.name)+' · '+esc(c.count)+'건</div></div>'
      +'<div class="pin-tail"></div></div>';
    var icon=L.divIcon({className:'',html:html,iconSize:[0,0],iconAnchor:[0,0]});
    L.marker([c.lat,c.lng],{icon:icon}).addTo(map).bindPopup(popupHtml(c),{maxWidth:340});
    pts.push([c.lat,c.lng]);
  });
  map.fitBounds(pts,{padding:[40,40],maxZoom:16});
})();
</script>

<!-- 5. 면책 조항 -->
<footer>
<p><strong>달성률 산정 기준(보수적)</strong>: 달성률은 <strong>투자 자산</strong>이 목표일에 목표 자산의 몇 %에 도달하는지를 뜻합니다. 보증금에 넣은 자기자본은 주거에 묶여 운용하지 못하는 기회비용으로 보아 예상자산에서 제외했고, 임대 종료 시 돌려받는 보증금 회수분은 더하지 않았습니다(실제 순자산은 보증금만큼 더 큼). 달성률 {최소달성률}% 미만 매물은 제외했습니다.<br><br>
본 리포트는 참고용이며 투자 조언이 아닙니다.<br>
실제 대출 금리, 매물 가격은 시점에 따라 변동됩니다.<br>
중요한 재무 결정은 전문가와 상담하시기 바랍니다.<br>
데이터 기준일: {YYYY-MM-DD}</p>
</footer>
</div>

<!-- 6. 테이블 헤더 클릭 정렬 JS -->
<script>
document.querySelectorAll('th[data-sort-type]').forEach(th => {
  th.style.cursor = 'pointer';
  th.addEventListener('click', function() {
    const table = th.closest('table');
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const idx = Array.from(th.parentNode.children).indexOf(th);
    const type = th.dataset.sortType;
    const asc = th.dataset.sortDir !== 'asc';
    th.dataset.sortDir = asc ? 'asc' : 'desc';
    table.querySelectorAll('th').forEach(h => h.textContent = h.textContent.replace(/ [▲▼]$/, ''));
    th.textContent += asc ? ' ▲' : ' ▼';
    rows.sort((a, b) => {
      let va = a.children[idx]?.textContent.trim() || '';
      let vb = b.children[idx]?.textContent.trim() || '';
      if (type === 'number') {
        va = parseFloat(va.replace(/[^0-9.\-]/g, '')) || 0;
        vb = parseFloat(vb.replace(/[^0-9.\-]/g, '')) || 0;
      }
      return asc ? (va > vb ? 1 : -1) : (va < vb ? 1 : -1);
    });
    rows.forEach(r => tbody.appendChild(r));
  });
});
</script>
</body>
</html>
```

### 디자인 원칙

- 위 참조 템플릿의 CSS와 HTML 구조를 그대로 사용한다. 데이터만 실제 값으로 교체한다.
- **지도 섹션을 제외하고는** 외부 CDN/라이브러리 없이 순수 HTML+CSS+인라인 JS로 구현한다. 지도 섹션만 Leaflet 1.9.4(unpkg CDN, SRI 핀)와 OpenStreetMap 타일을 사용한다. 지도는 별도 API 키가 필요 없으며, 오프라인일 때는 타일만 표시되지 않고 매물 표·마커 데이터는 영향받지 않는다(`typeof L === 'undefined'` 가드).
- 색상 체계: safe(녹색 `#e8f5e9`), warn(주황 `#fff3e0`), danger(빨강 `#ffebee`)
- 예상자산은 CSS 기반 바 차트(`.bar-container` + `.bar-fill`)로 시각화
- **달성률 구간(배지·바·밴드 공통)**: 100% 이상 = safe(🟢 안전), 85~100% = warn(🟡 절충), 70~85% = danger(🔴 공격). 70%(=`min_achievement_pct`) 미만은 표에 포함하지 않는다.
- 매물명은 네이버 부동산 매물 링크(`article_url`)로 연결, `target="_blank"`. 링크 뒤에 `[{구명}]`(gu_name)을 muted 텍스트로 병기한다.
- 달성률 구간 헤딩은 `<h3 class="band-{level}">`(`.band-safe/warn/danger` = 텍스트 색)을 사용한다.
- 테이블 헤더 클릭으로 열별 정렬 (숫자/텍스트 자동 판별)

### 지도 섹션 (표 아래 통합 지도)

매물 표 바로 아래에 단지 위치를 보여주는 통합 지도 1개를 둔다.

- **마커 단위 = 단지**: 최종 확정 매물(최대 100건)을 `complex_no`로 묶어(dedup) 단지당 마커 1개를 찍는다. 같은 단지의 좌표는 동일하므로 매물별로 찍으면 겹친다.
- **마커 라벨(가격표 핀)**: `월{최저월세}만` (그 단지 내 최저 월세) + `{단지명} · {매물수}건`.
- **마커 색 = 달성률**: 그 단지 매물 중 **최고 달성률** 기준 — 100%↑ `safe`(녹), 85~100% `warn`(주황), 70~85% `danger`(빨). 표의 배지 색 임계값과 동일하게 맞춘다.
- **클릭 팝업**: 단지명 · 세대수와, 그 단지 매칭 매물 목록(층/면적/보증금·월세/관리비/달성률 + 네이버 링크)을 표로 보여준다.
- **데이터 출처**: 각 매물의 `latitude`/`longitude`/`household_count`/`complex_no`(MCP가 단지 좌표를 부착). 좌표가 `null`인 단지는 지도에서만 제외하고 표에는 유지하며, 제외 건수를 `.map-note`에 명시한다(`"지도 미표시 단지 N개 (좌표 미확보)"`). 미표시 0건이면 주석을 비운다.
- **뷰포트**: 좌표가 있는 마커 전체에 `fitBounds`(자동 줌). 좌표 있는 단지가 0건이면 지도 대신 안내 문구를 표시한다.
- **마커 데이터 직렬화**: `COMPLEXES`(map.html 내 `<script>`)는 **유효한 JSON 배열 리터럴**로 작성한다 — 모든 문자열은 큰따옴표(`"`)로 감싸고 값 내부의 `"`·`\`만 escape(JSON은 JS 부분집합이라 `var COMPLEXES = [JSON];`로 그대로 동작). **작은따옴표 직렬화 금지**(단지명에 `'`가 있으면 스크립트가 깨진다). 배열이 3KB를 넘으면 `var COMPLEXES = [\n/*__ROWS__*/\n];`로 Write한 뒤 `old_string='/*__ROWS__*/'` → `new_string='{...},\n/*__ROWS__*/'`로 항목을 누적한다(분할 Write 규칙의 예외).
- **degradation**: 좌표 0건이면 지도 대신 안내 문구(템플릿이 처리), Leaflet 로드 실패(오프라인) 시 `typeof L` 가드로 안내. `minRent`/`rate`가 `null`·0이면 라벨/팝업에 `-`로 표기(템플릿 처리). 팝업 링크는 `safeUrl`로 `http(s)`만 허용한다.

## 출력 파일

HTML을 분할 생성한 후 Bash cat으로 조합한다. 각 파일은 3KB 이하로 제한한다(단, `map.html`의 `COMPLEXES` 데이터 블록은 단지 수에 따라 초과 가능 — Edit append로 누적).

```
{RUN_DIR}/
├── 03_report/
│   ├── header.html              # DOCTYPE + Leaflet CSS + 인라인 CSS + 헤더 + 매트릭스 + 대출요약 (~3KB)
│   ├── scenario_{id}.html       # 시나리오 섹션(표) (~2-3KB)
│   ├── map.html                 # 지도 섹션 + Leaflet JS + COMPLEXES 데이터 + 지도 init JS
│   └── footer.html              # 면책 조항 + 정렬 JS (~1KB)
└── housing_report.html          # 최종 조합 (Bash cat)
```

cat 조합 순서: `header.html → scenario_{id}.html → map.html → footer.html` (지도는 표 아래, 면책 위).

03_strategies.json은 생성하지 않는다 (HTML에 직접 포함).

## 면책 조항

리포트 하단에 반드시 포함:

```
본 리포트는 참고용이며 투자 조언이 아닙니다.
실제 대출 금리, 매물 가격은 시점에 따라 변동됩니다.
중요한 재무 결정은 전문가와 상담하시기 바랍니다.
데이터 기준일: YYYY-MM-DD
```
