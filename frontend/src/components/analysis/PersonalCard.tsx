import { User } from "lucide-react";
import type { CSSProperties } from "react";

import type { PersonalizedCheckpoints, UserProfile } from "../../services/backend_api/client";
import { readAuthSession } from "../../state/auth";
import "./personalCard.css";
import { useInView } from "./useInView";

interface PersonalCardProps {
  checkpoints: PersonalizedCheckpoints;
}

const riskLabels = {
  conservative: "안정형",
  balanced: "균형형",
  aggressive: "공격형",
} satisfies Record<UserProfile["risk_profile"], string>;

const horizonLabels = {
  short: "단기",
  medium: "중기",
  long: "장기",
} satisfies Record<UserProfile["investment_horizon"], string>;

const experienceLabels = {
  beginner: "초보",
  intermediate: "중급",
  experienced: "숙련",
} satisfies Record<UserProfile["experience_level"], string>;

function profileLabel(session: ReturnType<typeof readAuthSession>) {
  if (session?.profile) {
    const { risk_profile: risk, investment_horizon: horizon, experience_level: experience } = session.profile;
    return `${riskLabels[risk]} · ${horizonLabels[horizon]} · ${experienceLabels[experience]}`;
  }
  return session?.user.display_name?.trim() || "성향 미설정";
}

export function PersonalCard({ checkpoints }: PersonalCardProps) {
  const { ref, inView } = useInView<HTMLDivElement>();
  const session = readAuthSession();
  const username = session?.user.username ?? "회원";
  const checks = checkpoints.priority_checks.slice(0, 3);

  return (
    // motion 4b-13
    <div ref={ref} className={["analysis-personal-card", inView ? "analysis-personal-card--visible" : ""].join(" ")}>
      <div className="analysis-personal-card__header">
        <User size={20} strokeWidth={1.8} />
        <div>
          {username}님 성향({profileLabel(session)})엔 이게 걸려요
        </div>
      </div>
      <div className="analysis-personal-card__summary">{checkpoints.personal_summary}</div>
      {checks.length > 0 ? (
        <div className="analysis-personal-card__checks">
          {checks.map((check, index) => (
            <div key={`${index}-${check}`} className="analysis-personal-card__check" style={{ "--tile-delay": `${index * 90}ms` } as CSSProperties}>
              <span>{index + 1}</span> · {check}
            </div>
          ))}
        </div>
      ) : null}
      <div className="analysis-personal-card__caution">{checkpoints.caution || "주의: 커뮤니티 기대는 확인된 사실이 아니라 시장 반응이에요."}</div>
    </div>
  );
}
