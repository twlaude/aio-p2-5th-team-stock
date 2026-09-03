import type { LoginResponse } from "../services/backend_api/client";

const AUTH_STORAGE_KEY = "sallae.auth.session";

export interface AuthSession {
  token: string;
  tokenType: "bearer";
  user: LoginResponse["user"];
  profileCompleted: boolean;
}

function getStorage() {
  return typeof window === "undefined" ? null : window.localStorage;
}

export function readAuthSession(): AuthSession | null {
  const storage = getStorage();
  if (!storage) {
    return null;
  }

  const rawSession = storage.getItem(AUTH_STORAGE_KEY);
  if (!rawSession) {
    return null;
  }

  try {
    return JSON.parse(rawSession) as AuthSession;
  } catch {
    storage.removeItem(AUTH_STORAGE_KEY);
    return null;
  }
}

export function saveAuthSession(response: LoginResponse): AuthSession {
  const session: AuthSession = {
    token: response.access_token,
    tokenType: response.token_type,
    user: response.user,
    profileCompleted: response.profile_completed,
  };

  getStorage()?.setItem(AUTH_STORAGE_KEY, JSON.stringify(session));
  return session;
}

export function clearAuthSession() {
  getStorage()?.removeItem(AUTH_STORAGE_KEY);
}
