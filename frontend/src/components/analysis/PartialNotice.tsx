import { AlertCircle } from "lucide-react";

import "./partialNotice.css";

export type FailedKind = "community" | "news" | "disclosure";

const LABEL: Record<FailedKind, string> = { community: "커뮤니티", news: "뉴스", disclosure: "공시" };
const ALL: FailedKind[] = ["community", "news", "disclosure"];

/** 실제로 빠진 근거 섹션만 알린다. 데이터 섹션이 전부 정상이면(예: AI 설명만 실패해 규칙 문장으로 대체) 배너를 띄우지 않는다. */
export function PartialNotice({ failed }: { failed: FailedKind[] }) {
  if (failed.length === 0) {
    return null;
  }
  const missing = failed.map((kind) => LABEL[kind]).join("·");
  const kept = ["가격", ...ALL.filter((kind) => !failed.includes(kind)).map((kind) => LABEL[kind])].join("·");
  return (
    // motion 4b-17
    <div className="analysis-partial-notice">
      <AlertCircle size={18} strokeWidth={2} />
      <span>{`${missing} 데이터를 못 가져왔어요. ${kept}만으로 정리했어요.`}</span>
    </div>
  );
}
