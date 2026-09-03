import { useSearch } from "../../state/searchStore";

/** 영역 C 소유 — 근거 섹션(게이지·카드 3장·부분실패). id="evidence" 앵커는 B의 why 버튼이 사용. 아래는 스텁. */
export function EvidenceSection() {
  const { result, status } = useSearch();
  if (status !== "ready" || !result || result.status === "unsupported_company" || result.access_level !== "member" || !result.detail) {
    return null;
  }
  return (
    <section id="evidence" className="evidence">
      <p>시장 관심 온도 {result.detail.market_temperature.score} · 근거 {result.detail.evidence_level.level}</p>
    </section>
  );
}
