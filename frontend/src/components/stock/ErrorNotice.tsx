import { AlertTriangle } from "lucide-react";

import { Mascot } from "../mascot/Mascot";
import "./notice.css";

const fallbackMessage = "결과를 불러오지 못했어요. 잠시 후 다시 시도해 주세요.";

interface ErrorNoticeProps {
  message: string | null;
  onRetry: () => void;
}

export function ErrorNotice({ message, onRetry }: ErrorNoticeProps) {
  return (
    <section className="notice-stage notice-stage--error">
      <div className="error-notice" role="alert">
        <Mascot state="oops" size={64} />
        <AlertTriangle className="error-notice__icon" size={24} strokeWidth={2} aria-hidden="true" />
        <p>{message || fallbackMessage}</p>
        <button className="error-notice__button" type="button" onClick={onRetry}>
          다시 시도
        </button>
      </div>
    </section>
  );
}
