import { ArrowRight, Check, User } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import usersFixture from "../../mocks/users.json";
import { apiClient } from "../../services/backend_api";
import type { DemoUser, LoginResponse } from "../../services/backend_api/client";
import type { AuthSession } from "../../state/auth";
import { readPendingQuery } from "../../state/search";

const demoUsers = usersFixture as DemoUser[];

interface LoginPageProps {
  onLogin: (response: LoginResponse) => void;
  session: AuthSession | null;
}

export function LoginPage({ onLogin, session }: LoginPageProps) {
  const navigate = useNavigate();
  const [selectedUsername, setSelectedUsername] = useState(demoUsers[0]?.username ?? "demo001");
  const [loginResult, setLoginResult] = useState<LoginResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const selectedUser = demoUsers.find((user) => user.username === selectedUsername) ?? demoUsers[0];

  const handleLogin = async () => {
    setError(null);
    try {
      const response = await apiClient.login({ username: selectedUsername, password: "Demo1234!" });
      onLogin(response);
      setLoginResult(response);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "로그인하지 못했어요.");
    }
  };

  const pendingQuery = readPendingQuery();

  return (
    <section className="page-stack">
      <div className="page-heading">
        <div className="eyebrow">mock login</div>
        <h1 className="page-title">누구로 들어갈까요?</h1>
        <p className="page-copy">
          데모 계정 10개를 목 로그인 API로 확인해요. 비밀번호는 공통 <span className="mono">Demo1234!</span>
        </p>
      </div>

      <div className="user-grid">
        {demoUsers.map((demoUser) => (
          <button
            className="user-card"
            type="button"
            key={demoUser.username}
            aria-pressed={selectedUsername === demoUser.username}
            onClick={() => setSelectedUsername(demoUser.username)}
          >
            <span className="user-card__meta">
              <User size={18} aria-hidden="true" />
              {demoUser.username}
              {selectedUsername === demoUser.username ? <Check size={16} aria-hidden="true" /> : null}
            </span>
            <span className="user-card__name">{demoUser.display_name}</span>
          </button>
        ))}
      </div>

      <div className="control-row">
        <button className="pill-button pill-button--primary" type="button" onClick={handleLogin}>
          <ArrowRight size={16} aria-hidden="true" />
          {selectedUser.username}로 로그인
        </button>
        <button className="ghost-button" type="button" onClick={() => navigate("/")}>
          홈으로
        </button>
      </div>

      {pendingQuery ? <p className="page-copy">로그인 후 보던 {pendingQuery} 결과로 돌아갈 수 있어요.</p> : null}
      {session ? <p className="page-copy">현재 {session.user.display_name} 계정으로 로그인되어 있어요.</p> : null}
      {error ? <div className="error-copy">{error}</div> : null}

      <div className="json-grid">
        <JsonCard title="mock users fixture" value={demoUsers} />
        <JsonCard title="POST /api/v1/auth/login" value={loginResult} />
      </div>
    </section>
  );
}

interface JsonCardProps {
  title: string;
  value: unknown;
}

function JsonCard({ title, value }: JsonCardProps) {
  return (
    <article className="json-card">
      <h2 className="json-card__title">{title}</h2>
      <div className="json-card__body">
        <pre>{JSON.stringify(value ?? { status: "waiting" }, null, 2)}</pre>
      </div>
    </article>
  );
}
