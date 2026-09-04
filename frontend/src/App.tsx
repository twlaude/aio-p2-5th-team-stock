import { useEffect, useState } from "react";
import { Route, Routes } from "react-router-dom";

import { Nav } from "./components/common/Nav";
import { HomePage } from "./pages/home/HomePage";
import { LoginPage } from "./pages/login/LoginPage";
import type { LoginResponse, UserProfile } from "./services/backend_api/client";
import { AUTH_EXPIRED_EVENT } from "./services/backend_api/live";
import { clearAuthSession, readAuthSession, saveAuthSession, type AuthSession } from "./state/auth";
import { SearchProvider } from "./state/searchStore";

export function App() {
  const [session, setSession] = useState<AuthSession | null>(() => readAuthSession());

  const handleLogin = (response: LoginResponse, profile?: UserProfile) => {
    const nextSession = saveAuthSession(response, profile);
    setSession(nextSession);
  };

  const handleLogout = () => {
    clearAuthSession();
    setSession(null);
  };

  // 서버가 저장된 토큰을 거부하면(만료·시크릿 교체) live 어댑터가 세션을 지우고 이 이벤트를 쏜다 → 화면도 로그아웃 상태로.
  useEffect(() => {
    const onExpired = () => setSession(null);
    window.addEventListener(AUTH_EXPIRED_EVENT, onExpired);
    return () => window.removeEventListener(AUTH_EXPIRED_EVENT, onExpired);
  }, []);

  return (
    <div className="app-shell">
      <Nav session={session} onLogout={handleLogout} />
      <SearchProvider token={session?.token}>
        <main className="page-shell">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/login" element={<LoginPage onLogin={handleLogin} session={session} />} />
          </Routes>
        </main>
      </SearchProvider>
    </div>
  );
}
