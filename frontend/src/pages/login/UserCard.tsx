import { Check, User } from "lucide-react";
import { motion, useReducedMotion } from "motion/react";

import type { DemoUser } from "../../services/backend_api/client";

interface UserCardProps {
  user: DemoUser;
  selected: boolean;
  index: number;
  onSelect: () => void;
}

export function UserCard({ user, selected, index, onSelect }: UserCardProps) {
  const reducedMotion = useReducedMotion();

  return (
    <motion.button
      className="login-user-card"
      type="button"
      aria-pressed={selected}
      onClick={onSelect}
      initial={reducedMotion ? { opacity: 0 } : { opacity: 0, y: 12 }}
      animate={reducedMotion ? { opacity: 1 } : { opacity: 1, y: 0, scale: selected ? 1.03 : 1 }}
      transition={{ delay: reducedMotion ? 0 : index * 0.04, duration: 0.2 }}
    >
      {/* motion 4b-16 */}
      <span className="login-user-card__meta">
        <User size={18} strokeWidth={1.8} aria-hidden="true" />
        <span>{user.username}</span>
      </span>
      <span className="login-user-card__name">{user.display_name}</span>
      {selected ? (
        <motion.span
          className="login-user-card__check"
          initial={reducedMotion ? { opacity: 0 } : { opacity: 0, scale: 0.6 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.18 }}
        >
          <Check size={16} strokeWidth={2.2} aria-hidden="true" />
        </motion.span>
      ) : null}
    </motion.button>
  );
}
