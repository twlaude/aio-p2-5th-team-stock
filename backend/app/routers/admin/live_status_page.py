LIVE_STATUS_HTML = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>실황 — 살래? 말래?</title>
<style>
  body { font-family: -apple-system, "Malgun Gothic", sans-serif; background: #0b0f14; color: #e6edf3; margin: 0; padding: 24px; }
  h1 { font-size: 18px; margin: 0 0 4px; }
  .sub { color: #8b949e; font-size: 13px; margin-bottom: 20px; }
  .dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #3fb950; margin-right: 6px; animation: pulse 1.5s infinite; }
  @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.3; } }
  section { margin-bottom: 28px; }
  h2 { font-size: 14px; color: #58a6ff; border-bottom: 1px solid #21262d; padding-bottom: 6px; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th, td { text-align: left; padding: 6px 8px; border-bottom: 1px solid #21262d; white-space: nowrap; }
  th { color: #8b949e; font-weight: normal; }
  .status-success { color: #3fb950; }
  .status-partial_success { color: #d29922; }
  .status-timeout, .status-external_api_error, .status-internal_error { color: #f85149; }
  .fail-badge { display: inline-block; background: #3b1d1f; color: #f85149; border-radius: 4px; padding: 1px 6px; margin-right: 4px; font-size: 11px; }
  .empty { color: #6e7681; font-style: italic; }
  .new-row { animation: flash 1.2s ease-out; }
  @keyframes flash { 0% { background: #1f6feb33; } 100% { background: transparent; } }
</style>
</head>
<body>
  <h1><span class="dot"></span>실시간 실황</h1>
  <div class="sub" id="conn-status">연결 중...</div>

  <section>
    <h2>지금 활성 단기 Memory (Redis, TTL 30분)</h2>
    <table id="short-term-table">
      <thead><tr><th>user_id</th><th>최근 검색 종목</th><th>종목코드</th><th>검색 시각</th><th>남은 TTL</th></tr></thead>
      <tbody></tbody>
    </table>
  </section>

  <section>
    <h2>최근 분석 요청 (PostgreSQL analysis_runs)</h2>
    <table id="runs-table">
      <thead><tr><th>시각</th><th>사용자</th><th>종목</th><th>상태</th><th>부분 실패</th></tr></thead>
      <tbody></tbody>
    </table>
  </section>

<script>
const shortTermBody = document.querySelector('#short-term-table tbody');
const runsBody = document.querySelector('#runs-table tbody');
const connStatus = document.getElementById('conn-status');

function renderShortTerm(items) {
  shortTermBody.innerHTML = items.length
    ? items.map(i => `<tr>
        <td>${i.user_id}</td>
        <td>${i.recent_company_name ?? ''}</td>
        <td>${i.recent_stock_code ?? ''}</td>
        <td>${i.searched_at ?? ''}</td>
        <td>${i.ttl_seconds}s</td>
      </tr>`).join('')
    : '<tr><td colspan="5" class="empty">활성 키 없음</td></tr>';
}

function failBadges(failures) {
  if (!failures || failures.length === 0) return '-';
  return failures.map(f => `<span class="fail-badge">${f.service ?? '?'}: ${f.status ?? f.message ?? '실패'}</span>`).join(' ');
}

function prependRun(run, isNew) {
  const tr = document.createElement('tr');
  if (isNew) tr.className = 'new-row';
  tr.innerHTML = `
    <td>${run.requested_at ?? ''}</td>
    <td>${run.user_id ?? '비회원'}</td>
    <td>${run.company_name ?? ''} (${run.stock_code ?? ''})</td>
    <td class="status-${run.status}">${run.status}</td>
    <td>${failBadges(run.partial_failures)}</td>
  `;
  runsBody.prepend(tr);
  while (runsBody.children.length > 30) runsBody.removeChild(runsBody.lastChild);
}

async function loadSnapshot() {
  const res = await fetch('/api/v1/admin/live-status/snapshot');
  const data = await res.json();
  renderShortTerm(data.short_term);
  runsBody.innerHTML = '';
  data.recent_runs.forEach(run => prependRun(run, false));
}

function connect() {
  const es = new EventSource('/api/v1/admin/live-status/stream');
  es.onopen = () => { connStatus.textContent = '실시간 연결됨'; };
  es.onerror = () => { connStatus.textContent = '연결 끊김 · 재연결 시도 중...'; };
  es.onmessage = (ev) => {
    const event = JSON.parse(ev.data);
    if (event.type === 'analysis_run') {
      prependRun(event, true);
    } else if (event.type === 'short_term') {
      loadSnapshot();
    }
  };
}

loadSnapshot();
connect();
</script>
</body>
</html>
"""
