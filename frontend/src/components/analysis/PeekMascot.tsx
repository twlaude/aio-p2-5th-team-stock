import { useEffect, useState } from "react";

import { Mascot } from "../mascot/Mascot";
import "./peekMascot.css";

export function PeekMascot() {
  const [visible, setVisible] = useState(false);
  const [winking, setWinking] = useState(false);

  useEffect(() => {
    if (typeof document === "undefined") {
      return;
    }

    const evidence = document.getElementById("evidence");
    const personal = document.getElementById("personal");
    if (!evidence || typeof IntersectionObserver === "undefined") {
      setVisible(Boolean(evidence));
      return;
    }

    const evidenceObserver = new IntersectionObserver(
      ([entry]) => {
        if (entry?.isIntersecting) {
          setVisible(true);
        }
      },
      { threshold: 0.18 },
    );
    evidenceObserver.observe(evidence);

    let personalObserver: IntersectionObserver | null = null;
    if (personal) {
      personalObserver = new IntersectionObserver(
        ([entry]) => {
          setWinking(Boolean(entry?.isIntersecting));
        },
        { threshold: 0.25 },
      );
      personalObserver.observe(personal);
    }

    return () => {
      evidenceObserver.disconnect();
      personalObserver?.disconnect();
    };
  }, []);

  if (!visible) {
    return null;
  }

  return (
    // motion 4b-14
    <button className="analysis-peek-mascot" type="button" aria-label="맨 위로" onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}>
      <Mascot state={winking ? "wink" : "peek"} size={72} />
    </button>
  );
}
