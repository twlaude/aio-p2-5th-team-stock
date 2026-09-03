import { useSearch } from "../../state/searchStore";

/** 영역 C 소유 — 성향별 확인 포인트 + 푸터. 아래는 스텁. */
export function PersonalSection() {
  const { result, status } = useSearch();
  if (status !== "ready" || !result || result.status === "unsupported_company" || result.access_level !== "member" || !result.personalized_checkpoints) {
    return null;
  }
  return (
    <section className="personal">
      <p>{result.personalized_checkpoints.personal_summary}</p>
    </section>
  );
}
