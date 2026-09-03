import { useState } from "react";
import { Route, Routes } from "react-router-dom";

import { Nav } from "./components/common/Nav";
import { HomePage } from "./pages/home/HomePage";
import { LoginPage } from "./pages/login/LoginPage";
import type { LoginResponse } from "./services/backend_api/client";
import { clearAuthSession, readAuthSession, saveAuthSession, type AuthSession } from "./state/auth";

export function App() {
  const [session, setSession] = useState<AuthSession | null>(() => readAuthSession());

  const handleLogin = (response: LoginResponse) => {
    const nextSession = saveAuthSession(response);
    setSession(nextSession);
  };

  const handleLogout = () => {
    clearAuthSession();
    setSession(null);
  };

  return (
    <div className="app-shell">
      <Nav session={session} onLogout={handleLogout} />
      <main className="page-shell">
        <Routes>
          <Route path="/" element={<HomePage session={session} />} />
          <Route path="/login" element={<LoginPage onLogin={handleLogin} session={session} />} />
        </Routes>
      </main>
    </div>
  );
}
