import companiesFixture from "../../mocks/companies.json";
import samsungFixture from "../../mocks/analyses/samsung.json";
import templateFixture from "../../mocks/analyses/templates.json";
import usersFixture from "../../mocks/users.json";
import type {
  AnalysisDetail,
  AnalysisRequest,
  AnalysisResponse,
  AnalysisSource,
  BackendApiClient,
  CompaniesResponse,
  Company,
  DataCoverage,
  DemoUser,
  DemoUsersFixture,
  EvidenceLevel,
  GuestAnalysisResponse,
  LoginRequest,
  LoginResponse,
  MemberAnalysisResponse,
  PersonalizedCheckpoints,
  PriceSnapshot,
  ProfileResponse,
  TopicPreview,
  UserProfile,
} from "./client";

export type MockScenario = "partial" | "unsupported" | "slow" | "error" | null;

interface MockClientOptions {
  delayMs?: number;
  scenario?: MockScenario;
}

interface SamsungFixture {
  guest: Omit<GuestAnalysisResponse, "request_id">;
  member_detail: AnalysisDetail;
  member_profiles: Record<string, PersonalizedCheckpoints>;
  partial_detail: AnalysisDetail;
  error: {
    message: string;
  };
}

interface TemplateAnalysis {
  company_name: string;
  stock_code: string;
  current_price: number;
  change: number;
  change_rate: number;
  temperature_score: number;
  temperature_label: string;
  evidence_level: EvidenceLevel;
  topic: string;
}

const DEMO_PASSWORD = "Demo1234!";
const SNAPSHOT_DATE = "2026-09-01";
const TOKEN_PREFIX = "demo-token-";

const companies = companiesFixture as Company[];
const users = (usersFixture as DemoUsersFixture).users;
const samsung = samsungFixture as SamsungFixture;
const templates = templateFixture as TemplateAnalysis[];

function sleep(ms: number) {
  return new Promise((resolve) => globalThis.setTimeout(resolve, ms));
}

function clone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T;
}

function requestId() {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }

  return `mock-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function runtimeScenario(): MockScenario {
  if (typeof window === "undefined") {
    return null;
  }

  const scenario = new URLSearchParams(window.location.search).get("scenario");
  if (scenario === "partial" || scenario === "unsupported" || scenario === "slow" || scenario === "error") {
    return scenario;
  }

  return null;
}

function normalizeQuery(query: string) {
  return query.trim().replace(/\s+/g, "").toLowerCase();
}

function findCompany(query: string) {
  const normalized = normalizeQuery(query);
  return companies.find((company) => {
    const normalizedName = normalizeQuery(company.company_name);
    return normalized === company.stock_code || normalized === normalizedName || normalizedName.includes(normalized);
  });
}

function findTemplate(company: Company) {
  return templates.find((template) => template.stock_code === company.stock_code);
}

function getUserFromToken(token?: string) {
  if (!token) {
    return null;
  }

  const bareToken = token.replace(/^Bearer\s+/i, "");
  const username = bareToken.startsWith(TOKEN_PREFIX) ? bareToken.slice(TOKEN_PREFIX.length) : "";
  return users.find((user) => user.username === username) ?? null;
}

function profileOf(user: DemoUser): UserProfile {
  return {
    experience_level: user.experience_level,
    risk_profile: user.risk_profile,
    investment_horizon: user.investment_horizon,
    preferred_evidence: user.preferred_evidence,
  };
}

function profileKey(user: DemoUser) {
  return `${user.risk_profile}-${user.investment_horizon}`;
}

function unsupportedResponse(query: string): AnalysisResponse {
  return {
    status: "unsupported_company",
    message: `아직 ${query || "입력한 기업"} 분석은 제공하지 않아요. 현재는 2026년 9월 1일 기준 코스피 시가총액 상위 20개 기업만 지원하고 있어요.`,
    actions: ["지원 기업 20개 보기", "다른 종목 검색하기"],
  };
}

function companyPayload(company: Company) {
  return {
    company_name: company.company_name,
    stock_code: company.stock_code,
    supported: true,
  };
}

function templatePrice(template: TemplateAnalysis): PriceSnapshot {
  return {
    current_price: template.current_price,
    change: template.change,
    change_rate: template.change_rate,
    as_of: "2026-09-01T06:30:00Z",
  };
}

function buildTemplateTopics(template: TemplateAnalysis): TopicPreview[] {
  return [
    { text: template.topic, sentiment: "positive", weight: 5 },
    { text: "실적 확인", sentiment: "neutral", weight: 4 },
    { text: "수급 변화", sentiment: template.change >= 0 ? "positive" : "negative", weight: 4 },
    { text: "가격 부담", sentiment: "negative", weight: 3 },
    { text: "공시 일정", sentiment: "neutral", weight: 3 },
    { text: "뉴스 반복", sentiment: "neutral", weight: 2 },
    { text: "단기 변동", sentiment: "negative", weight: 2 },
    { text: "시장 관심", sentiment: "positive", weight: 3 },
  ];
}

function buildTemplateNewsSources(company: Company, template: TemplateAnalysis): AnalysisSource[] {
  return [
    { type: "news", title: `${company.company_name} ${template.topic} 관련 보도`, publisher: "Mock News", published_at: "2026-09-01T02:30:00Z", url: "https://example.com/mock-news-1", meta: { issue_count: 2 } },
    { type: "news", title: `${company.company_name} 업종 수급 변화 분석`, publisher: "Mock Market", published_at: "2026-08-31T06:00:00Z", url: "https://example.com/mock-news-2" },
    { type: "news", title: `${template.topic} 기대와 가격 부담 동시 점검`, publisher: "Mock Economy", published_at: "2026-08-31T03:10:00Z", url: "https://example.com/mock-news-3" },
    { type: "news", title: `${company.company_name} 실적 발표 전 확인 포인트`, publisher: "Mock Securities", published_at: "2026-08-30T07:40:00Z", url: "https://example.com/mock-news-4" },
    { type: "news", title: `${company.company_name} 단기 변동성 확대 가능성`, publisher: "Mock Daily", published_at: "2026-08-30T01:20:00Z", url: "https://example.com/mock-news-5" },
  ];
}

function buildTemplateDisclosureSources(company: Company, template: TemplateAnalysis): AnalysisSource[] {
  return [
    { type: "disclosure", title: `${company.company_name} 주요사항보고서`, publisher: "Mock DART", published_at: "2026-08-29T08:00:00Z", url: "https://example.com/mock-disclosure-1", meta: { receipt_no: `20260829${company.stock_code}`, confirmed: [`${template.topic} 관련 공개 자료`, "최근 재무 지표 제출", "주요 사업 현황 공시"], unconfirmed: ["다음 분기 실적 반영 폭", "단기 가격 촉매 지속성", "시장 기대와 실제 숫자의 차이"] } },
    { type: "disclosure", title: `${company.company_name} 반기보고서`, publisher: "Mock DART", published_at: "2026-08-20T08:00:00Z", url: "https://example.com/mock-disclosure-2", meta: { receipt_no: `20260820${company.stock_code}` } },
    { type: "disclosure", title: `${company.company_name} 기업설명회 자료`, publisher: "Mock DART", published_at: "2026-08-14T08:00:00Z", url: "https://example.com/mock-disclosure-3", meta: { receipt_no: `20260814${company.stock_code}` } },
  ];
}

function buildTemplateDetail(company: Company, template: TemplateAnalysis, partial = false): AnalysisDetail {
  const coverage: DataCoverage[] = partial ? ["price", "news", "disclosure"] : ["price", "news", "disclosure", "community"];
  return {
    market_temperature: {
      score: partial ? Math.max(40, template.temperature_score - 8) : template.temperature_score,
      label: partial ? "일부 확인" : template.temperature_label,
      data_coverage: coverage,
    },
    evidence_level: {
      level: partial ? "medium" : template.evidence_level,
      reason: partial ? "커뮤니티 반응을 제외하고 뉴스와 공시 중심으로 확인했어요." : `${template.topic} 관련 공개 자료를 함께 확인했어요.`,
    },
    news_summary: `${company.company_name} 관련 뉴스는 ${template.topic} 흐름을 중심으로 살펴봐야 해요.`,
    disclosure_summary: `${company.company_name}의 최근 공시는 실적과 투자 계획을 확인하는 데 초점이 있어요.`,
    community_summary: partial ? null : "커뮤니티 반응은 사실이 아닌 시장 반응으로만 참고해야 해요.",
    sources: [
      ...buildTemplateNewsSources(company, template),
      ...buildTemplateDisclosureSources(company, template),
      ...(partial
        ? []
        : [
            {
              type: "community" as const,
              title: `${company.company_name} 시장 반응 표본`,
              publisher: "Mock Community",
              published_at: "2026-09-01T04:00:00Z",
              meta: {
                samples: 128,
                positive: 46,
                neutral: 34,
                negative: 20,
                fgi: 59,
                topics: buildTemplateTopics(template),
              },
            },
          ]),
    ],
  };
}

function buildTemplateResponse(company: Company, user: DemoUser, partial = false): MemberAnalysisResponse {
  const template = findTemplate(company);
  if (!template) {
    return clone({
      ...samsung.guest,
      request_id: requestId(),
      access_level: "member",
      requires_login: false,
      detail: partial ? samsung.partial_detail : samsung.member_detail,
      personalized_checkpoints: samsung.member_profiles[profileKey(user)],
    });
  }

  return {
    request_id: requestId(),
    status: partial ? "partial_completed" : "success",
    access_level: "member",
    requires_login: false,
    company: companyPayload(company),
    price: templatePrice(template),
    one_line_summary: `${company.company_name}은 ${template.topic}을 중심으로 확인할 흐름이 보여요.`,
    detail: buildTemplateDetail(company, template, partial),
    personalized_checkpoints: samsung.member_profiles[profileKey(user)],
  };
}

function buildGuestResponse(company: Company): GuestAnalysisResponse {
  if (company.stock_code === "005930") {
    return {
      ...clone(samsung.guest),
      request_id: requestId(),
    };
  }

  const template = findTemplate(company);
  return {
    request_id: requestId(),
    status: "success",
    access_level: "guest",
    requires_login: true,
    company: companyPayload(company),
    price: template
      ? templatePrice(template)
      : {
          current_price: 0,
          change: 0,
          change_rate: 0,
          as_of: "2026-09-01T06:30:00Z",
        },
    one_line_summary: template ? `${company.company_name}은 ${template.topic}을 중심으로 살펴봐야 해요.` : "공개 데이터로 확인할 내용을 정리했어요.",
    detail: null,
    personalized_checkpoints: null,
    topics_preview: template ? buildTemplateTopics(template) : undefined,
  };
}

function buildSamsungMember(user: DemoUser, partial = false): MemberAnalysisResponse {
  return {
    ...clone(samsung.guest),
    request_id: requestId(),
    status: partial ? "partial_completed" : "success",
    access_level: "member",
    requires_login: false,
    detail: partial ? clone(samsung.partial_detail) : clone(samsung.member_detail),
    personalized_checkpoints: clone(samsung.member_profiles[profileKey(user)]),
  };
}

async function maybeDelay(scenario: MockScenario, delayMs: number) {
  const effectiveDelay = scenario === "slow" ? 2200 : delayMs;
  if (effectiveDelay > 0) {
    await sleep(effectiveDelay);
  }
}

export function createMockClient(options: MockClientOptions = {}): BackendApiClient {
  const delayMs = options.delayMs ?? 0;

  return {
    health: async () => ({ status: "ok" }),
    login: async (request: LoginRequest): Promise<LoginResponse> => {
      await maybeDelay(null, delayMs || 400);
      const user = users.find((candidate) => candidate.username === request.username);
      if (!user || request.password !== DEMO_PASSWORD) {
        throw new Error("데모 계정 정보를 확인해 주세요.");
      }

      return {
        status: "success",
        access_token: `${TOKEN_PREFIX}${user.username}`,
        token_type: "bearer",
        user: {
          user_id: user.user_id,
          username: user.username,
          display_name: user.display_name,
        },
        profile_completed: true,
      };
    },
    getProfile: async (token: string): Promise<ProfileResponse> => {
      const user = getUserFromToken(token);
      if (!user) {
        throw new Error("로그인이 필요해요.");
      }

      return {
        status: "success",
        profile: profileOf(user),
      };
    },
    updateProfile: async (token: string, profile: UserProfile): Promise<ProfileResponse> => {
      const user = getUserFromToken(token);
      if (!user) {
        throw new Error("로그인이 필요해요.");
      }

      return {
        status: "success",
        profile,
      };
    },
    getCompanies: async (): Promise<CompaniesResponse> => ({
      status: "success",
      snapshot_date: SNAPSHOT_DATE,
      companies: clone(companies),
    }),
    createAnalysis: async (request: AnalysisRequest, token?: string): Promise<AnalysisResponse> => {
      const scenario = options.scenario ?? runtimeScenario();
      await maybeDelay(scenario, delayMs);

      if (scenario === "error") {
        throw new Error(samsung.error.message);
      }

      const company = scenario === "unsupported" ? null : findCompany(request.query);
      if (!company) {
        return unsupportedResponse(request.query);
      }

      const user = getUserFromToken(token);
      if (!user) {
        return buildGuestResponse(company);
      }

      if (company.stock_code === "005930") {
        return buildSamsungMember(user, scenario === "partial");
      }

      return buildTemplateResponse(company, user, scenario === "partial");
    },
  };
}

export const mockApiClient = createMockClient();
