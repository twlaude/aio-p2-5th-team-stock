import { LogIn, LogOut, User } from "lucide-react";
import { Link } from "react-router-dom";

import type { AuthSession } from "../../state/auth";
import { apiMode } from "../../services/backend_api";

interface NavProps {
  session: AuthSession | null;
  onLogout: () => void;
}

export function Nav({ session, onLogout }: NavProps) {
  return (
    <header className="nav">
      <Link className="nav__brand" to="/" aria-label="살래? 말래? 홈">
        살래<span className="nav__brand-mark">?</span> 말래<span className="nav__brand-mark">?</span>
      </Link>
      <div className="nav__actions">
        <div className="nav__caption">{apiMode === "live" ? "실데이터 데모 · 투자 권유 아님" : "Mock 데이터 · 실제 투자 정보 아님"}</div>
        {session ? (
          <>
            <div className="user-pill" aria-label={`${session.user.display_name} 로그인됨`}>
              <User size={16} aria-hidden="true" />
              <span className="user-pill__username">{session.user.username}</span>
              <span className="user-pill__display-name">{session.user.display_name}</span>
            </div>
            <button className="ghost-button" type="button" onClick={onLogout} aria-label="로그아웃">
              <LogOut size={16} aria-hidden="true" />
              <span className="ghost-button__label">로그아웃</span>
            </button>
          </>
        ) : (
          <Link className="pill-button" to="/login">
            <LogIn size={16} aria-hidden="true" />
            로그인
          </Link>
        )}
      </div>
    </header>
  );
}
