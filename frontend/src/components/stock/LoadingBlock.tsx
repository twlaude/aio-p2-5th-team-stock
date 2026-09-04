import { Check } from "lucide-react";
import { useEffect, useState } from "react";

import { Mascot } from "../mascot/Mascot";
import "./loadingBlock.css";

const progressItems = ["가격", "뉴스", "공시", "커뮤니티"];

function prefersReducedMotion() {
  return typeof window !== "undefined"
    && typeof window.matchMedia === "function"
    && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

export function LoadingBlock() {
  const [completedCount, setCompletedCount] = useState(() => (prefersReducedMotion() ? progressItems.length : 0));

  // motion 4b-5
  useEffect(() => {
    if (prefersReducedMotion()) {
      setCompletedCount(progressItems.length);
      return undefined;
    }

    setCompletedCount(0);
    const timers = progressItems.map((_, index) => window.setTimeout(() => setCompletedCount(index + 1), (index + 1) * 500));
    return () => timers.forEach((timer) => window.clearTimeout(timer));
  }, []);

  return (
    <section className="loading-block" aria-live="polite">
      <div className="loading-block__mascot-row">
        <Mascot state="thinking" size={96} />
        <div className="loading-block__bubble" aria-hidden="true">
          <span className="loading-block__dot loading-block__dot--one" />
          <span className="loading-block__dot loading-block__dot--two" />
          <span className="loading-block__dot loading-block__dot--three" />
        </div>
      </div>
      <p className="loading-block__copy">뉴스 · 공시 · 커뮤니티 반응을 모으는 중이에요 (보통 10초 안팎)</p>
      <div className="loading-block__progress">
        {progressItems.map((item, index) => {
          const completed = index < completedCount;
          return (
            <span className={`loading-block__chip${completed ? " loading-block__chip--done" : " loading-block__chip--wait"}`} key={item}>
              {item}
              {completed ? (
                <>
                  <Check className="loading-block__check" size={14} strokeWidth={2.2} aria-hidden="true" />
                  <span className="loading-block__done">완료</span>
                </>
              ) : (
                <span className="loading-block__wait">…</span>
              )}
            </span>
          );
        })}
      </div>
      <div className="loading-block__skeleton" aria-hidden="true">
        <span className="loading-block__line loading-block__line--short" />
        <span className="loading-block__line loading-block__line--long" />
      </div>
    </section>
  );
}
