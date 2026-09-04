import type {
  AnalysisRequest,
  AnalysisResponse,
  BackendApiClient,
  CompaniesResponse,
  HealthResponse,
  LoginRequest,
  LoginResponse,
  ProfileResponse,
  UserProfile,
} from "./client";

import { clearAuthSession } from "../../state/auth";

/** 서버가 저장된 토큰을 거부했을 때(만료·서버 시크릿 교체) 던진다. */
export class StaleTokenError extends Error {
  constructor(path: string) {
    super(`API 401: ${path}`);
    this.name = "StaleTokenError";
  }
}

/** 로그인 세션이 무효해져 지웠음을 App에 알리는 window 이벤트 이름. */
export const AUTH_EXPIRED_EVENT = "sallae:auth-expired";

function dropStaleSession() {
  clearAuthSession();
  if (typeof window !== "undefined") {
    window.dispatchEvent(new Event(AUTH_EXPIRED_EVENT));
  }
}

async function requestJson<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init.headers,
    },
  });

  if (response.status === 401 && init.headers && "Authorization" in init.headers) {
    // 브라우저에 남은 옛 토큰(만료·백엔드 JWT 시크릿 교체 후)은 계속 401이므로 여기서 지운다.
    dropStaleSession();
    throw new StaleTokenError(path);
  }

  if (!response.ok) {
    throw new Error(`API ${response.status}: ${path}`);
  }

  return (await response.json()) as T;
}

function toProfileResponse(profile: UserProfile): ProfileResponse {
  return { status: "success", profile };
}

function authHeaders(token: string) {
  return {
    Authorization: `Bearer ${token}`,
  };
}

export function createLiveClient(): BackendApiClient {
  return {
    health: () => requestJson<HealthResponse>("/health"),
    login: (body: LoginRequest) =>
      requestJson<LoginResponse>("/api/v1/auth/login", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    // 백엔드 /api/v1/profile 은 성향 4필드를 flat 으로 돌려준다 → 화면 계약(ProfileResponse) 으로 감싼다.
    getProfile: (token: string) =>
      requestJson<UserProfile>("/api/v1/profile", {
        headers: authHeaders(token),
      }).then(toProfileResponse),
    updateProfile: (token: string, body: UserProfile) =>
      requestJson<UserProfile>("/api/v1/profile", {
        method: "PUT",
        headers: authHeaders(token),
        body: JSON.stringify(body),
      }).then(toProfileResponse),
    getCompanies: () => requestJson<CompaniesResponse>("/api/v1/companies"),
    createAnalysis: async (body: AnalysisRequest, token?: string) => {
      const request = (auth?: string) =>
        requestJson<AnalysisResponse>("/api/v1/analyses", {
          method: "POST",
          headers: auth ? authHeaders(auth) : undefined,
          body: JSON.stringify(body),
        });
      if (!token) {
        return request();
      }
      try {
        return await request(token);
      } catch (cause) {
        if (cause instanceof StaleTokenError) {
          return request(); // 옛 토큰은 지웠고, 비회원 결과로 이어서 보여준다(로그인 게이트가 자연히 뜸)
        }
        throw cause;
      }
    },
  };
}
