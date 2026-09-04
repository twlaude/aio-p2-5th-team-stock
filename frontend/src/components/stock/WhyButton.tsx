import { ChevronDown, MessageCircleQuestion } from "lucide-react";

import "./why-button.css";

interface WhyButtonProps {
  onClick: () => void;
}

export function WhyButton({ onClick }: WhyButtonProps) {
  return (
    <div className="why-button-wrap">
      {/* motion 4b-9 / motion 4b-18 */}
      <button className="why-button" type="button" onClick={onClick}>
        <MessageCircleQuestion size={22} strokeWidth={2.2} aria-hidden="true" />
        <span>왜 이렇게 판단했나요?</span>
      </button>
      <ChevronDown className="why-button-wrap__chevron" size={20} strokeWidth={2} aria-hidden="true" />
    </div>
  );
}
