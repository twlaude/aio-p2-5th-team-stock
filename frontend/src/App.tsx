import { useState } from "react";
import { Route, Routes } from "react-router-dom";

import { Nav } from "./components/common/Nav";
import { HomePage } from "./pages/home/HomePage";
import { LoginPage } from "./pages/login/LoginPage";
import type { LoginResponse, UserProfile } from "./services/backend_api/client";
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
