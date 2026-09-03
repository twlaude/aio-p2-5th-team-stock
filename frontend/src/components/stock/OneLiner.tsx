import { motion, useReducedMotion } from "motion/react";

import { Typewriter } from "../common/Typewriter";
import "./one-liner.css";

interface OneLinerProps {
  text: string;
}

export function OneLiner({ text }: OneLinerProps) {
  const reducedMotion = useReducedMotion();

  return (
    <div className="one-liner">
      <motion.div
        className="one-liner__caption"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.2 }}
      >
        우리는 지금 이렇게 보고 있어요!
      </motion.div>
      <motion.div
        className="one-liner__bubble"
        initial={reducedMotion ? { opacity: 0 } : { opacity: 0, scale: 0.9 }}
        animate={reducedMotion ? { opacity: 1 } : { opacity: 1, scale: 1 }}
        transition={reducedMotion ? { duration: 0.2 } : { type: "spring", stiffness: 320, damping: 18, delay: 0.12 }}
      >
        {/* motion 4b-8 */}
        <Typewriter text={text} startDelayMs={260} />
      </motion.div>
    </div>
  );
}
