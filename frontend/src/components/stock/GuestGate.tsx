import { Lock } from "lucide-react";
import { motion, useReducedMotion } from "motion/react";
import { useNavigate } from "react-router-dom";

import { savePendingQuery } from "../../state/search";
import { Mascot } from "../mascot/Mascot";
import "./guest-gate.css";

interface GuestGateProps {
  companyName: string;
  query: string;
}

export function preparePendingReturn(query: string): string {
  savePendingQuery(query);
  return "/login";
}

export function GuestGate({ companyName, query }: GuestGateProps) {
  const navigate = useNavigate();
  const reducedMotion = useReducedMotion();

  return (
    <motion.section
      id="guest-gate"
      className="guest-gate"
      initial={reducedMotion ? { opacity: 0 } : { opacity: 0, y: 16 }}
      animate={reducedMotion ? { opacity: 1 } : { opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <div className="guest-gate__blur" aria-hidden="true">
        <div className="guest-gate__dummy-grid">
          <article className="guest-gate__dummy-card">
            <div className="guest-gate__dummy-caption">시장 관심 온도</div>
            <div className="guest-gate__dummy-score"><span>82</span><strong>뜨거움</strong></div>
            <div className="guest-gate__bar"><span className="guest-gate__bar-fill" /></div>
            <div className="guest-gate__dummy-copy">커뮤니티 언급량 · 뉴스 기사량 · 거래량 변화 기준. 상승 가능성이 아니에요.</div>
          </article>
          <article className="guest-gate__dummy-card">
            <div className="guest-gate__dummy-caption">공시·보고서로 확인된 정도</div>
            <div className="guest-gate__dummy-score"><span>보통</span></div>
            <div className="guest-gate__segments"><span /><span /><i /></div>
            <div className="guest-gate__dummy-copy">최근 공시에서 메모리 투자는 확인, 파운드리 수익성은 미확인.</div>
          </article>
        </div>
      </div>
      <div className="guest-gate__card">
        <Mascot state="reveal" size={88} />
        <h2>회원가입이 필요합니다!</h2>
        <p>근거와 내 성향에 맞춘 확인 포인트는<br />로그인한 회원에게만 보여드려요.</p>
        <button type="button" onClick={() => navigate(preparePendingReturn(query))}>
          <Lock size={18} aria-hidden="true" />
          Mock 계정으로 로그인
        </button>
        <div>로그인하면 {companyName} 결과로 바로 돌아와요</div>
      </div>
    </motion.section>
  );
}
