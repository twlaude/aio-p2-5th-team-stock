import { AlertCircle } from "lucide-react";

import "./partialNotice.css";

export function PartialNotice() {
  return (
    // motion 4b-17
    <div className="analysis-partial-notice">
      <AlertCircle size={18} strokeWidth={2} />
      <span>커뮤니티 데이터를 못 가져왔어요. 뉴스·공시·가격만으로 정리했어요.</span>
    </div>
  );
}
