export type ApiMode = "mock" | "live";
export type AnalysisStatus = "success" | "partial_success" | "unsupported_company";
export type AccessLevel = "guest" | "member";
export type RiskProfile = "conservative" | "balanced" | "aggressive";
export type InvestmentHorizon = "short" | "medium" | "long";
export type ExperienceLevel = "beginner" | "intermediate" | "experienced";
export type PreferredEvidence = "financial" | "market" | "news" | "risk";
export type DataCoverage = "price" | "news" | "disclosure" | "community";
export type SourceType = "news" | "disclosure" | "community";
export type EvidenceLevel = "low" | "medium" | "high";

export interface HealthResponse {
  status: "ok" | "success";
}

export interface UserProfile {
  experience_level: ExperienceLevel;
  risk_profile: RiskProfile;
  investment_horizon: InvestmentHorizon;
  preferred_evidence: PreferredEvidence;
}

/** backend/app/data/mock_users.json 과 동일 구조 (성향 4필드 flat) */
export interface DemoUser extends UserProfile {
  user_id: string;
  username: string;
  display_name: string;
}

export interface DemoUsersFixture {
  users: DemoUser[];
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  status: "success";
  access_token: string;
  token_type: "bearer";
  user: {
    user_id: string;
    username: string;
    display_name: string;
  };
  profile_completed: boolean;
}

export interface ProfileResponse {
  status: "success";
  profile: UserProfile;
}

export interface Company {
  rank: number;
  company_name: string;
  stock_code: string;
  market: "KOSPI" | "KOSDAQ";
}

export interface CompaniesResponse {
  status: "success";
  snapshot_date: string;
  companies: Company[];
}

export interface AnalysisRequest {
  query: string;
  question?: string;
}

export interface AnalysisCompany {
  company_name: string;
  stock_code: string;
  supported: boolean;
}

export interface PriceSnapshot {
  current_price: number;
  change: number;
  change_rate: number;
  as_of: string;
  volume_basis?: string | null;
  volume_as_of?: string | null;
}

export interface AnalysisSource {
  source_type: DataCoverage;
  title: string;
  published_at?: string;
  url?: string;
  meta?: Record<string, unknown>;
}

export interface AnalysisDetail {
  market_temperature: {
    score: number;
    label: string;
    data_coverage: DataCoverage[];
    weight_covered: number;
  };
  evidence_level: {
    level: EvidenceLevel;
    reason: string;
  };
  news_summary: string | null;
  disclosure_summary: string | null;
  community_summary: string | null;
  sources: AnalysisSource[];
}

export interface PersonalizedCheckpoints {
  personal_summary: string;
  priority_checks: string[];
  caution: string;
}

export interface TopicPreview {
  text: string;
  sentiment: "positive" | "neutral" | "negative";
  weight: 1 | 2 | 3 | 4 | 5;
}

export interface GuestAnalysisResponse {
  request_id: string;
  status: "success";
  access_level: "guest";
  requires_login: true;
  company: AnalysisCompany;
  price: PriceSnapshot;
  one_line_summary: string;
  detail: null;
  personalized_checkpoints: null;
  /** 계약(shared/contracts/frontend_backend) 밖 — 비회원 결과 주변 앰비언트 키워드용 mock 전용 표시 필드. 라이브 백엔드엔 없음(undefined). */
  topics_preview?: TopicPreview[];
}

export interface MemberAnalysisResponse {
  request_id: string;
  status: "success" | "partial_success";
  access_level: "member";
  requires_login: false;
  company: AnalysisCompany;
  price: PriceSnapshot;
  one_line_summary: string;
  detail: AnalysisDetail;
  personalized_checkpoints: PersonalizedCheckpoints;
}

export interface UnsupportedCompanyResponse {
  status: "unsupported_company";
  message: string;
  actions: string[];
}

export type AnalysisResponse = GuestAnalysisResponse | MemberAnalysisResponse | UnsupportedCompanyResponse;

export interface BackendApiClient {
  health: () => Promise<HealthResponse>;
  login: (request: LoginRequest) => Promise<LoginResponse>;
  getProfile: (token: string) => Promise<ProfileResponse>;
  updateProfile: (token: string, profile: UserProfile) => Promise<ProfileResponse>;
  getCompanies: () => Promise<CompaniesResponse>;
  createAnalysis: (request: AnalysisRequest, token?: string) => Promise<AnalysisResponse>;
}
