---
name: strategy-report
description: "부동산 월세 전략 비교 리포트 생성. 재무 시뮬레이션과 매물 데이터를 종합하여 9가지 시나리오(목표 자산 3가지 × 월 수익률 3가지)별 월세 TOP 20을 HTML 리포트로 작성. 주거 전략, 대출 전략, 투자 전략 비교표, 자산 변화 그래프 포함. 부동산 리포트, 주거 전략 리포트 요청 시 반드시 이 스킬을 사용할 것."
---

# Strategy Report

재무 시뮬레이션의 9가지 시나리오(목표 자산 3가지 × 월 수익률 3가지)별 최대 가능 금액 내에서, 가장 공격적인(비싼) 월세 TOP 20 매물을 추천하는 HTML 리포트를 생성하는 스킬.

## 리포트 원칙

### 1. 구성: 9가지 시나리오별 월세 TOP 20

각 시나리오별로 매물을 면적 내림차순으로 정렬하여, 목표 자산에 도달 가능한 범위 내에서 가장 비싼 매물 20개를 선정한다.

### 2. 각 매물에 포함할 정보

```
- 매물명 (네이버 부동산 링크), 층수, 면적(평수)
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

관리비 참고:
- `maintenance_fee_10k` — 네이버 부동산 단지 상세에서 평형별 연평균 관리비를 조회한다
- 관리비가 0이면 리포트에 "-" 로 표시한다
- 관리비는 매물별로 다르므로 시나리오 매트릭스에는 포함하지 않고 "관리비 별도" 주석을 표시한다

### 3. 매물 정렬 규칙

- 월세: 면적 내림차순 (동일 면적이면 보증금 내림차순, 동일 보증금이면 월세 오름차순)
- 목표 달성률이 100% 미만이면 경고 표시

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
.report-table .name-cell{text-align:left;max-width:180px;overflow:hidden;text-overflow:ellipsis}
.report-table a{color:#1565c0;text-decoration:none}
.report-table a:hover{text-decoration:underline}
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
</style>
</head>
<body>
<div class="container">

<!-- 1. 헤더: 제목 + 생성일자 + 조건 요약 그리드 -->
<header>
<h1>주거 전략 리포트 — {지역명} 아파트 월세</h1>
<p style="opacity:0.8;font-size:14px">데이터 기준일: {YYYY-MM-DD} | 분석 대상: {평수범위} 아파트 월세</p>
<div class="conditions">
<div class="cond-item"><div class="cond-label">총 자산</div><div class="cond-value">{총자산}</div></div>
<div class="cond-item"><div class="cond-label">목표 자산</div><div class="cond-value">{목표1} / {목표2} / {목표3}</div></div>
<div class="cond-item"><div class="cond-label">월 수익률</div><div class="cond-value">{수익률1} / {수익률2} / {수익률3}</div></div>
<div class="cond-item"><div class="cond-label">투자 기간</div><div class="cond-value">{N}개월 ({시작}~{종료})</div></div>
<div class="cond-item"><div class="cond-label">대출 한도</div><div class="cond-value">{대출한도}</div></div>
<div class="cond-item"><div class="cond-label">실질 대출금리</div><div class="cond-value">연 {실질금리}% (회사지원 반영)</div></div>
</div>
</header>

<!-- 2. 시나리오 매트릭스: 3×3 테이블 -->
<div class="matrix">
<h2>시나리오 매트릭스 — 9가지 조합 요약</h2>
<table>
<thead>
<tr><th rowspan="2">목표 자산</th><th colspan="3">월 수익률</th></tr>
<tr><th>{수익률1}</th><th>{수익률2}</th><th>{수익률3}</th></tr>
</thead>
<tbody>
<!-- 각 셀에 class="safe|warn|danger" 적용 -->
<!-- 셀 내용: 보증금 X억<br>월세 Y만 + 이자 Z만<br>= 월 주거비 W만 -->
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

<!-- 4. 시나리오별 매물 TOP 20 (9개 반복) -->
<div class="scenario-section">
<h2>시나리오: 목표 {목표}억 / 월 수익률 {수익률}%</h2>
<div class="scenario-meta">여유도: <span class="badge-{level}">{label}</span> | 최대 보증금: {보증금} | 최대 월세: {월세} | 매물 {N}건</div>
<div class="report-container">
<table class="report-table">
<thead><tr>
<th data-sort-type="number">#</th>
<th data-sort-type="text">매물명</th>
<th data-sort-type="text">층</th>
<th data-sort-type="number">면적(평)</th>
<th data-sort-type="text">등록일</th>
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
<td class="name-cell"><a href="{article_url}" target="_blank">{매물명}</a></td>
<td>{층}</td>
<td>{면적}</td>
<td>{등록일}</td>
<td>{보증금}/{월세}</td>
<td>{관리비}만</td>
<td>대출 {대출액}<br>자기자본 {자기자본}</td>
<td>{대출이자}만</td>
<td>{월주거비}만</td>
<td>{투자금}</td>
<td><div class="bar-container"><div class="bar-fill bar-{level}" style="width:{pct}%">{예상자산}</div></div></td>
<td><span class="badge-{level}">{달성률}%</span></td>
</tr>
<!-- ... 20건 반복 -->
</tbody>
</table>
</div>
</div>
<!-- ... 9개 시나리오 반복 -->

<!-- 5. 면책 조항 -->
<footer>
<p>본 리포트는 참고용이며 투자 조언이 아닙니다.<br>
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
- 외부 CDN/라이브러리 없이 순수 HTML+CSS+인라인 JS로 구현한다.
- 색상 체계: safe(녹색 `#e8f5e9`), warn(주황 `#fff3e0`), danger(빨강 `#ffebee`)
- 예상자산은 CSS 기반 바 차트(`.bar-container` + `.bar-fill`)로 시각화
- 달성률 100% 이상 = badge-safe, 90~100% = badge-warn, 90% 미만 = badge-danger
- 매물명은 네이버 부동산 매물 링크(`article_url`)로 연결, `target="_blank"`
- 테이블 헤더 클릭으로 열별 정렬 (숫자/텍스트 자동 판별)

## 출력 파일

HTML을 분할 생성한 후 Bash cat으로 조합한다. 각 파일은 3KB 이하로 제한한다.

```
{RUN_DIR}/
├── 03_report/
│   ├── header.html              # DOCTYPE + CSS + 헤더 + 매트릭스 + 대출요약 (~3KB)
│   ├── scenario_{id}.html       # 시나리오별 섹션 (각 ~2-3KB)
│   └── footer.html              # 면책 조항 + 정렬 JS (~1KB)
└── housing_report.html          # 최종 조합 (Bash cat)
```

03_strategies.json은 생성하지 않는다 (HTML에 직접 포함).

## 면책 조항

리포트 하단에 반드시 포함:

```
본 리포트는 참고용이며 투자 조언이 아닙니다.
실제 대출 금리, 매물 가격은 시점에 따라 변동됩니다.
중요한 재무 결정은 전문가와 상담하시기 바랍니다.
데이터 기준일: YYYY-MM-DD
```
