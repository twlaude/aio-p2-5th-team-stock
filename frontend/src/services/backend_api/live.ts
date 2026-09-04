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

async function requestJson<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`API ${response.status}: ${path}`);
  }

  return (await response.json()) as T;
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
    getProfile: (token: string) =>
      requestJson<ProfileResponse>("/api/v1/profile", {
        headers: authHeaders(token),
      }),
    updateProfile: (token: string, body: UserProfile) =>
      requestJson<ProfileResponse>("/api/v1/profile", {
        method: "PUT",
        headers: authHeaders(token),
        body: JSON.stringify(body),
      }),
    getCompanies: () => requestJson<CompaniesResponse>("/api/v1/companies"),
    createAnalysis: (body: AnalysisRequest, token?: string) =>
      requestJson<AnalysisResponse>("/api/v1/analyses", {
        method: "POST",
        headers: token ? authHeaders(token) : undefined,
        body: JSON.stringify(body),
      }),
  };
}
