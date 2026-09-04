import { motion, useReducedMotion } from "motion/react";

import type { AnalysisCompany, PriceSnapshot } from "../../services/backend_api/client";
import { CountUp, formatDecimal, formatSignedDecimal, formatSignedRate } from "../common/CountUp";
import "./price-header.css";

interface PriceHeaderProps {
  company: AnalysisCompany;
  price: PriceSnapshot;
}

const seoulTimeFormatter = new Intl.DateTimeFormat("ko-KR", {
  timeZone: "Asia/Seoul",
  hour: "2-digit",
  minute: "2-digit",
  hour12: false,
});

export function PriceHeader({ company, price }: PriceHeaderProps) {
  const reducedMotion = useReducedMotion();
  const changeClass = price.change >= 0 ? "price-header__change--up" : "price-header__change--down";
  const changeMotion = reducedMotion
    ? { initial: { opacity: 0 }, animate: { opacity: 1 } }
    : { initial: { opacity: 0, scale: 0.8 }, animate: { opacity: 1, scale: 1 } };

  return (
    <div className="price-header">
      <div className="price-header__identity">
        <div className="price-header__market">{company.stock_code} · KOSPI</div>
        <div className="price-header__name">{company.company_name}</div>
      </div>
      <div className="price-header__quote">
        <div className="price-header__value">
          <CountUp value={price.current_price} format={formatDecimal} />
          <span className="price-header__unit">원</span>
        </div>
        <motion.div
          className={`price-header__change ${changeClass}`}
          {...changeMotion}
          transition={{ delay: reducedMotion ? 0 : 0.2, duration: 0.2 }}
        >
          {/* motion 4b-6 */}
          {formatSignedDecimal(price.change)} ({formatSignedRate(price.change_rate)})
          <span className="price-header__time"> · {seoulTimeFormatter.format(new Date(price.as_of))} 기준</span>
        </motion.div>
      </div>
    </div>
  );
}
