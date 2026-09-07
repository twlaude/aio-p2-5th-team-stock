_HTML_TEMPLATE = """<!DOCTYPE html>
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
  .mcp-links { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px; }
  .mcp-links a { color: #58a6ff; background: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 6px 10px; text-decoration: none; font-size: 13px; }
  .mcp-links a:hover { border-color: #58a6ff; }
  pre { background: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 10px 12px; font-size: 12px; overflow-x: auto; }
  .hint { color: #8b949e; font-size: 12px; margin-top: 6px; }
  .desc { color: #8b949e; font-size: 12px; }
  .guide { background: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 12px; font-size: 13px; }
</style>
</head>
<body>
  <h1><span class="dot"></span>실시간 실황</h1>
  <div class="sub" id="conn-status">연결 중...</div>
  <p class="guide">이 페이지는 살래말래 서버가 지금 어떤 상태인지 보는 곳. 뭔가 안 되면 ① 서비스 상태판 → ② DB/Redis → ③ 실패 기록 순서로 보면 원인이 좁혀진다.</p>
  <div class="sub" id="system-updated">시스템 현황 조회 중...</div>

  <section>
    <h2>서비스 상태판</h2>
    <p class="desc">우리 서비스를 이루는 서버 5개가 살아있는지. 분석이 안 돌거나 느리면 여기부터. 빨간 게 있으면 그 서버가 죽은 것.</p>
    <table><thead><tr><th>이름</th><th>하는 일</th><th>상태</th><th>응답 ms</th><th>비고</th></tr></thead><tbody id="services-body"></tbody></table>
  </section>

  <section>
    <h2>MCP 서버 직접 확인 (MCP Inspector)</h2>
    <p class="desc">위 표만으로 부족할 때 MCP 서버에 직접 툴을 호출해 보는 방법.</p>
    <div class="mcp-links">{{MCP_LINKS}}</div>
    <div class="hint">Node.js 있는 컴퓨터에서 아래 명령으로 Inspector를 띄운 뒤, Transport를 "Streamable HTTP"로 두고 위 주소 중 하나를 넣으면 Tool 목록·직접 호출·raw 응답까지 볼 수 있다.</div>
    <pre>npx @modelcontextprotocol/inspector</pre>
  </section>

  <section>
    <h2>PostgreSQL</h2>
    <p class="desc">분석 기록·회원·공시 데이터가 쌓이는 DB. 데이터가 안 쌓이거나 로그인이 안 되면 여기.</p>
    <p id="postgres-status"></p>
    <table><thead><tr><th>DB 이름</th><th>용량 MB</th><th>접속 수</th></tr></thead><tbody id="databases-body"></tbody></table>
    <table><thead><tr><th>테이블 (백엔드 DB)</th><th>row 수</th></tr></thead><tbody id="tables-body"></tbody></table>
    <table><thead><tr><th>전체</th><th>24시간</th><th>24시간 성공률</th><th>마지막 요청 시각</th></tr></thead><tbody id="analysis-body"></tbody></table>
  </section>

  <section>
    <h2>Redis</h2>
    <p class="desc">회원이 최근에 뭘 검색했는지 30분간만 기억하는 임시 저장소 + 실시간 이벤트 통로. 아래 '활성 단기 Memory'가 비어 있는데 방금 검색이 있었다면 여기 상태를 의심.</p>
    <p id="redis-status"></p>
    <table><thead><tr><th>연결</th><th>키 개수</th><th>단기메모리 키 수</th><th>메모리 사용량</th><th>접속 클라이언트</th><th>가동일수</th><th>마지막 이벤트 시각</th></tr></thead><tbody id="redis-body"></tbody></table>
  </section>

  <section>
    <h2>지금 활성 단기 Memory (Redis, TTL 30분)</h2>
    <p class="desc">지금 이 순간 누가 어떤 종목을 봤는지 (30분 지나면 사라짐).</p>
    <table id="short-term-table">
      <thead><tr><th>user_id</th><th>최근 검색 종목</th><th>종목코드</th><th>검색 시각</th><th>남은 TTL</th></tr></thead>
      <tbody></tbody>
    </table>
  </section>

  <section>
    <h2>최근 분석 요청 (PostgreSQL analysis_runs)</h2>
    <p class="desc">사용자가 종목 분석을 누를 때마다 한 줄. 여기 안 뜨면 요청이 백엔드까지 못 온 것.</p>
    <table id="runs-table">
      <thead><tr><th>시각</th><th>사용자</th><th>종목</th><th>상태</th><th>부분 실패</th></tr></thead>
      <tbody></tbody>
    </table>
  </section>

  <section>
    <h2>최근 실패 기록</h2>
    <p class="desc">실패했거나 일부 서버가 답을 못 준 분석만 모은 것. 같은 서버 이름이 반복되면 그 서버가 문제.</p>
    <p id="failures-status" class="desc"></p>
    <table><thead><tr><th>서버</th><th>최근 7일 실패 횟수</th></tr></thead><tbody id="failure-counts-body"></tbody></table>
    <table><thead><tr><th>시각</th><th>사용자</th><th>종목</th><th>상태</th><th>실패한 서버</th></tr></thead><tbody id="failures-body"></tbody></table>
  </section>

<script>
const escapeHtml = value => String(value ?? '-').replace(/[&<>"']/g, c => ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}[c]));
const statusHtml = ok => `<span class="status-${ok ? 'success' : 'internal_error'}">${ok ? 'ok' : 'down'}</span>`;
function fillTable(id, rows, columns, empty = '기록 없음') {
  document.getElementById(id).innerHTML = rows.length
    ? rows.map(row => `<tr>${row.map(cell => `<td>${cell}</td>`).join('')}</tr>`).join('')
    : `<tr><td colspan="${columns}" class="empty">${escapeHtml(empty)}</td></tr>`;
}
function blockStatus(id, block, label) {
  const node = document.getElementById(id);
  node.className = `status-${block.ok ? 'success' : 'internal_error'}`;
  node.textContent = block.ok ? `${label} 연결 정상 ${block.version ?? ''}` : `${label} 조회 실패: ${block.error}`;
}
async function loadSystem() {
  const updated = document.getElementById('system-updated');
  try {
    const res = await fetch('/api/v1/admin/live-status/system');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    fillTable('services-body', data.services.map(s => {
      const notes = [s.detail?.mock ? '가짜 데이터 모드' : '', s.detail?.openai_configured === false ? 'OpenAI 키 없음' : '', s.detail?.error ?? (s.status === 'down' ? JSON.stringify(s.detail) : '')].filter(Boolean);
      return [escapeHtml(s.name), escapeHtml(s.role), statusHtml(s.status === 'ok'), escapeHtml(s.latency_ms), `<span class="status-partial_success">${escapeHtml(notes.join(' · ') || '-')}</span>`];
    }), 5);
    const pg = data.postgres, r = data.redis, a = pg.analysis;
    blockStatus('postgres-status', pg, 'PostgreSQL');
    blockStatus('redis-status', r, 'Redis');
    fillTable('databases-body', pg.databases.map(d => [d.name, d.size_mb, d.connections].map(escapeHtml)), 3, '조회할 수 없음');
    fillTable('tables-body', pg.tables.map(t => [t.name, t.rows].map(escapeHtml)), 2, '조회할 수 없음');
    fillTable('analysis-body', pg.ok ? [[`${a.total}건`, `${a.last_24h}건`, a.success_rate_24h == null ? '-' : `${a.success_rate_24h}%`, a.last_requested_at].map(escapeHtml)] : [], 4, '조회할 수 없음');
    fillTable('redis-body', [[statusHtml(r.ok), ...[r.keys_in_db, r.short_term_keys, r.used_memory_human, r.connected_clients, r.uptime_days, r.last_event_at].map(value => escapeHtml(r.ok ? value : null))]], 7);
    document.getElementById('failures-status').textContent = pg.ok ? '' : 'PostgreSQL 조회 실패로 실패 기록을 확인할 수 없음';
    fillTable('failure-counts-body', data.failures.by_service_7d.map(f => [f.service, f.count].map(escapeHtml)), 2, pg.ok ? '기록 없음' : '조회할 수 없음');
    fillTable('failures-body', data.failures.recent.map(run => [
      ...[run.requested_at, run.user_id ?? '비회원', `${run.company_name} (${run.stock_code})`, run.status].map(escapeHtml),
      failBadges((run.partial_failures ?? []).map(f => Object.fromEntries(Object.entries(f).map(([key, value]) => [key, escapeHtml(value)]))))
    ]), 5, pg.ok ? '기록 없음' : '조회할 수 없음');
    updated.textContent = `시스템 현황 갱신: ${new Date(data.checked_at).toLocaleTimeString('en-GB', {hour12: false})}`;
    updated.className = 'sub';
  } catch (error) {
    updated.textContent = `시스템 현황 갱신 실패: ${error.message} · 표시된 값은 이전 조회 결과 · 30초 후 재시도`;
    updated.className = 'sub status-internal_error';
  }
}
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

function buildRunRow(run, isNew) {
  const tr = document.createElement('tr');
  if (isNew) tr.className = 'new-row';
  tr.innerHTML = `
    <td>${run.requested_at ?? ''}</td>
    <td>${run.user_id ?? '비회원'}</td>
    <td>${run.company_name ?? ''} (${run.stock_code ?? ''})</td>
    <td class="status-${run.status}">${run.status}</td>
    <td>${failBadges(run.partial_failures)}</td>
  `;
  return tr;
}

function prependRun(run) {
  runsBody.prepend(buildRunRow(run, true));
  while (runsBody.children.length > 30) runsBody.removeChild(runsBody.lastChild);
}

async function loadSnapshot() {
  const res = await fetch('/api/v1/admin/live-status/snapshot');
  const data = await res.json();
  renderShortTerm(data.short_term);
  runsBody.innerHTML = '';
  // recent_runs는 서버에서 이미 requested_at DESC(최신순)로 온다 — append로 그 순서를 그대로 유지한다.
  data.recent_runs.forEach(run => runsBody.appendChild(buildRunRow(run, false)));
}

function connect() {
  const es = new EventSource('/api/v1/admin/live-status/stream');
  es.onopen = () => { connStatus.textContent = '실시간 연결됨'; };
  es.onerror = () => { connStatus.textContent = '연결 끊김 · 재연결 시도 중...'; };
  es.onmessage = (ev) => {
    const event = JSON.parse(ev.data);
    if (event.type === 'analysis_run') {
      prependRun(event);
    } else if (event.type === 'short_term') {
      loadSnapshot();
    }
  };
}

loadSystem();
setInterval(loadSystem, 30000);
loadSnapshot();
connect();
</script>
</body>
</html>
"""


def render_live_status_html(mcp_urls: dict[str, str]) -> str:
    links = " ".join(
        f'<a href="{url}" target="_blank" rel="noreferrer">{name}</a>' for name, url in mcp_urls.items()
    )
    return _HTML_TEMPLATE.replace("{{MCP_LINKS}}", links)
