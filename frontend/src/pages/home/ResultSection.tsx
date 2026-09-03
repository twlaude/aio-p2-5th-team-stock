import { useSearch } from "../../state/searchStore";

/** 영역 B 소유 — 공개 결과(가격·스파크라인·한줄결론·why)·비회원 게이트. 아래는 스텁. */
export function ResultSection() {
  const { result, status } = useSearch();
  if (status !== "ready" || !result || result.status === "unsupported_company") {
    return null;
  }
  return (
    <section className="result">
      <h2>{result.company.company_name} {result.company.stock_code}</h2>
      <p>{result.price.current_price.toLocaleString()}원 ({result.price.change_rate}%)</p>
      <p>{result.one_line_summary}</p>
      <a href="#evidence">왜 이렇게 판단했나요?</a>
    </section>
  );
}
