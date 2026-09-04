import { FileText, MessageCircle, Newspaper, TrendingUp } from "lucide-react";
import { motion, useReducedMotion } from "motion/react";

import { Typewriter } from "../common/Typewriter";
import "./one-liner.css";

export interface OneLinerMaterials {
  news?: number;
  disclosure?: number;
  community?: number;
}

interface OneLinerProps {
  text: string;
  /** 한 문장에 취합된 재료 개수(회원 detail.sources 기준). 없으면 라벨만 표시(비회원). */
  materials?: OneLinerMaterials;
}

const MATERIALS = [
  { key: "price", label: "가격", Icon: TrendingUp },
  { key: "news", label: "뉴스", Icon: Newspaper },
  { key: "disclosure", label: "공시", Icon: FileText },
  { key: "community", label: "커뮤니티", Icon: MessageCircle },
] as const;

export function OneLiner({ text, materials }: OneLinerProps) {
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
      <motion.div
        className="one-liner__materials"
        aria-label="한 문장에 취합한 재료"
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, delay: reducedMotion ? 0.2 : 1.1 }}
      >
        {MATERIALS.map(({ key, label, Icon }) => {
          const count = key === "price" ? undefined : materials?.[key];
          return (
            <span className="one-liner__material" key={key}>
              <Icon size={13} strokeWidth={2} aria-hidden="true" />
              {label}
              {typeof count === "number" ? <strong>{count}건</strong> : null}
            </span>
          );
        })}
        <span className="one-liner__material">모아서 한마디</span>
      </motion.div>
    </div>
  );
}
