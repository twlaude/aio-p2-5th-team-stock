/**
 * 앰비언트 칩용 주제 축약. 커뮤니티 MCP는 "낸드 가격 상승에 따른 실적 개선" 같은 8~18자 구절을 주는데,
 * 결론 주변 칩은 10자 안팎이어야 링 배치가 안 겹친다(2026-09-04 오현님 요청: 겹침 → 요약해서 짧게).
 * 규칙(결정적, LLM 없음):
 *  1) 마침표·"~를 기대한다/우려한다" 류 서술 어미 제거
 *  2) 이미 MAX 이하면 그대로
 *  3) 연결어("에 따른", "과/와/의/및/후/관련" 토큰) 뒤쪽 핵심 명사구를 남김. 뒤쪽이 너무 짧으면 앞쪽을 남김
 *  4) 그래도 길면 뒤 단어부터 떼어냄. 한 단어인데 길면 잘라서 "…"
 */
export const TOPIC_MAX_CHARS = 11;

const TRAILING_PREDICATE = /\s*(?:[을를이가은는도])?\s*(?:기대|우려|걱정|염려|주목|언급|예상|전망)(?:한다|된다|함|됨|이다|다|중)\s*[.。]?$/u;
const CONNECTIVE_TOKEN = /^(?:.+[과와의]|따른|및|후|관련|대비|위한|통한)$/u;

function joinTokens(tokens: string[]): string {
  return tokens.join(" ").trim();
}

export function shortenTopic(raw: string, max = TOPIC_MAX_CHARS): string {
  let text = raw.trim().replace(/[.。!]+$/u, "");
  const stripped = text.replace(TRAILING_PREDICATE, "").trim();
  if (stripped.length >= 2) text = stripped;
  if (text.length <= max) return text;

  const tokens = text.split(/\s+/u).filter(Boolean);
  // 연결어 기준으로 뒤쪽(핵심) 또는 앞쪽(주어)만 남기기 — 뒤에서부터 찾아야 가장 짧은 핵심구가 나온다
  for (let i = tokens.length - 2; i >= 0; i -= 1) {
    if (!CONNECTIVE_TOKEN.test(tokens[i])) continue;
    const tail = joinTokens(tokens.slice(i + 1));
    if (tail.length >= 4 && tail.length <= max) return tail;
    const headTokens = tokens.slice(0, i + 1);
    const last = headTokens[headTokens.length - 1];
    if (/[과와의]$/u.test(last) && last.length > 1) headTokens[headTokens.length - 1] = last.slice(0, -1);
    else if (CONNECTIVE_TOKEN.test(last)) headTokens.pop();
    const head = joinTokens(headTokens);
    if (head.length >= 4 && head.length <= max) return head;
    if (tail.length > max) {
      const inner = shortenTopic(tail, max);
      if (inner.length >= 4) return inner;
    }
  }

  // 뒤 단어부터 떼어내기 ("매입·소각"처럼 가운뎃점으로 묶인 건 뒤쪽부터)
  const kept = [...tokens];
  while (joinTokens(kept).length > max) {
    const last = kept[kept.length - 1];
    if (last.includes("·")) kept[kept.length - 1] = last.slice(0, last.lastIndexOf("·"));
    else if (kept.length > 1) kept.pop();
    else break;
  }
  const result = joinTokens(kept);
  if (result.length <= max) return result;
  return `${result.slice(0, max - 1)}…`;
}
