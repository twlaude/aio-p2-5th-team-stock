import { ArrowRight } from "lucide-react";
import { motion, useReducedMotion } from "motion/react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { Mascot } from "../../components/mascot/Mascot";
import usersFixture from "../../mocks/users.json";
import { apiClient } from "../../services/backend_api";
import type { DemoUsersFixture, LoginResponse, UserProfile } from "../../services/backend_api/client";
import type { AuthSession } from "../../state/auth";
import { readPendingQuery } from "../../state/search";
import { UserCard } from "./UserCard";
import "./login.css";

const demoUsers = (usersFixture as DemoUsersFixture).users;

interface LoginPageProps {
  onLogin: (response: LoginResponse, profile?: UserProfile) => void;
  session: AuthSession | null;
}

export function LoginPage({ onLogin, session }: LoginPageProps) {
  const navigate = useNavigate();
  const reducedMotion = useReducedMotion();
  const [selectedUsername, setSelectedUsername] = useState(demoUsers[0].username);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const selectedUser = demoUsers.find((user) => user.username === selectedUsername) ?? demoUsers[0];
  const pendingQuery = readPendingQuery();

  const handleLogin = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.login({ username: selectedUser.username, password: "Demo1234!" });
      const profile = await apiClient.getProfile(response.access_token).then((profileResponse) => profileResponse.profile).catch(() => undefined);
      onLogin(response, profile);
      navigate("/");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "로그인하지 못했어요.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.section
      className="login-page"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: reducedMotion ? 0.01 : 0.2 }}
    >
      {/* motion 4b-16 */}
      <Mascot state="idle" size={96} />
      <h1>누구로 들어갈까요?</h1>
      <p className="login-page__copy">
        투자 성향이 미리 들어 있는 데모 계정 10개예요. 비밀번호는 공통 <span className="mono">Demo1234!</span>
      </p>
      {session ? <p className="login-page__session">지금은 {session.user.display_name} 계정이에요</p> : null}
      <div className="login-page__users">
        {demoUsers.map((user, index) => (
          <UserCard
            index={index}
            key={user.username}
            selected={selectedUsername === user.username}
            user={user}
            onSelect={() => setSelectedUsername(user.username)}
          />
        ))}
      </div>
      <button className="login-page__submit" type="button" disabled={loading} onClick={handleLogin}>
        <span>{loading ? "로그인 중…" : `${selectedUser.username}로 로그인`}</span>
        <ArrowRight size={16} aria-hidden="true" />
      </button>
      {error ? <div className="login-page__error">{error}</div> : null}
      <div className="login-page__caption">
        {pendingQuery
          ? `로그인 후 보던 ${pendingQuery} 결과로 돌아가요 · 실제 회원가입은 이번 범위 아님`
          : "실제 회원가입은 이번 범위 아님"}
      </div>
    </motion.section>
  );
}
