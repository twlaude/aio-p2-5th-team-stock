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

type GapState = "large" | "some" | "small" | "quiet";

/** 한글 조사 선택: 받침 있으면 a, 없으면 b (영문·숫자로 끝나면 b) */
function josa(word: string, a: string, b: string) {
  const code = word.charCodeAt(word.length - 1);
  if (code >= 0xac00 && code <= 0xd7a3) return `${word}${(code - 0xac00) % 28 ? a : b}`;
  return `${word}${b}`;
}

const RISK_WORD: Record<DemoUser["risk_profile"], string> = { conservative: "손실을 피하는 걸 우선하는", balanced: "적당한 위험은 감수하는", aggressive: "큰 변동도 감수하는" };
const HORIZON_WORD: Record<DemoUser["investment_horizon"], string> = { long: "오래 들고 가는", medium: "몇 달 보고 가는", short: "짧게 치고 빠지는" };

function gapState(score: number, level: EvidenceLevel): GapState {
  if (score >= 70 && level === "low") return "large";
  if ((score >= 65 && level === "medium") || (score >= 78 && level !== "low")) return "some";
  if (score < 50 && level === "high") return "quiet";
  return "small";
}

/** 목 모드 개인화 — "당신은 ○○ 성향이고, 이 종목은 지금 ○○ 상태라서 ○○" 구조. 실서비스에선 MCP Client가 성향+공통 분석으로 생성. */
function composePersonal(company: string, topic: string, score: number, level: EvidenceLevel, user: DemoUser): PersonalizedCheckpoints {
  const state = gapState(score, level);
  const you = `${RISK_WORD[user.risk_profile]} ${HORIZON_WORD[user.investment_horizon]} 편`;
  // 첫 문장 = 포인트(크게), 뒷문장 = 부연(작게). 화면(PersonalCard)이 첫 문장에서 나눈다.
  const C = josa(company, "은", "는");
  const T = (a: string, b: string) => josa(topic, a, b);
  const opinion: Record<GapState, Record<DemoUser["risk_profile"], string>> = {
    large: {
      conservative: `지금은 지켜보는 게 나아요. ${C} ${topic} 기대만 앞서 있고 공시로 확인된 건 거의 없어요. ${you}인 당신에겐 맞지 않는 구간이에요.`,
      balanced: `지금 사면 비싸게 살 수 있어요. ${C} ${topic} 기대가 앞서 있어서, ${you}이라면 공시로 확인되는 걸 보고 나눠서 접근하는 게 맞아요.`,
      aggressive: `들어간다면 나갈 기준부터 정하세요. ${C} ${topic} 기대만으로 움직이는 구간이라 크게 흔들릴 수 있어요. ${you}이라도 기준 없이 들어가면 위험해요.`,
    },
    some: {
      conservative: `당신에겐 '아직'이에요. ${C} 관심은 뜨겁고 ${T("은", "는")} 절반쯤 확인됐어요. ${you}이라면 다음 실적으로 확인되고 나서 봐도 늦지 않아요.`,
      balanced: `한 번에 말고 나눠서 보세요. ${C} ${topic} 중 확인된 절반은 볼 만하고 나머지는 기대예요. ${you}이라면 확인되는 만큼만 따라가는 게 맞아요.`,
      aggressive: `해볼 만한 구간이에요. ${C} ${T("이", "가")} 절반은 확인됐어요. 다만 ${you}이라도 기대가 꺾이면 빠르게 되돌아올 수 있다는 걸 기억하세요.`,
    },
    small: {
      conservative: `무리 없는 구간이에요. ${C} 관심과 확인된 재료가 비슷해요. ${you}인 당신은 ${topic} 실적 흐름만 꾸준히 보면 돼요.`,
      balanced: `평소 기준대로 보면 돼요. ${C} 지금 앞서가는 신호가 없어요. ${you}이라면 ${T("을", "를")} 중심으로 차분히 접근해도 돼요.`,
      aggressive: `급하게 움직일 이유는 없어요. ${C} ${topic} 대비 관심이 과하지 않아요. ${you}이라면 새 촉매가 나오는지 지켜보세요.`,
    },
    quiet: {
      conservative: `당신에게 잘 맞는 편이에요. ${C} 조용하지만 ${T("이", "가")} 공식 자료로 탄탄해요. ${you}이라면 서두르지 않고 천천히 봐도 돼요.`,
      balanced: `관심 가져볼 만해요. ${C} 관심이 낮아 가격 부담이 적고 ${T("은", "는")} 확인돼 있어요. ${you}이라면 지금 살펴보기 좋은 구간이에요.`,
      aggressive: `기다릴지 먼저 정하세요. ${C} 아직 관심이 없어서 움직임이 느릴 수 있어요. ${you}이라면 촉매가 나올 때까지 지루할 수 있어요.`,
    },
  };
  const horizonCheck: Record<DemoUser["investment_horizon"], string> = {
    long: "배당·현금흐름이 유지되는지",
    medium: "다음 분기 실적이 지난 분기보다 나아졌는지",
    short: "하루 변동 폭과 거래량이 견딜 만한지",
  };
  const stateCheck: Record<GapState, string> = {
    large: `${josa(topic, "이", "가")} 공시로 확인되는지 (지금은 기사뿐)`,
    some: `${topic} 중 아직 확인 안 된 절반이 언제 확인되는지`,
    small: `${topic} 관련 새 소식이 확인된 것인지`,
    quiet: `${topic}에 시장이 언제 관심을 갖기 시작하는지`,
  };
  const caution: Record<DemoUser["risk_profile"], string> = {
    conservative: "기대가 높을 땐 급하게 따라 사지 않아도 괜찮아요. 확인하고 들어가도 늦지 않아요.",
    balanced: "뉴스와 커뮤니티가 같이 뜨거우면 한 박자 쉬어가도 돼요.",
    aggressive: "뉴스만으로 오른 종목은 되돌림이 빨라요. 욕심보다 기준이 먼저예요.",
  };
  return {
    personal_summary: opinion[state][user.risk_profile],
    priority_checks: ["다음 실적 발표 날짜와 결과", stateCheck[state], horizonCheck[user.investment_horizon]],
    caution: caution[user.risk_profile],
  };
}

/** 목 모드 한줄 결론 — 실서비스에선 MCP Client의 LLM이 4개 재료(가격·뉴스·공시·커뮤니티)를 취합해 만든다. 여기선 같은 재료로 조합만. */
function composeOneLiner(template: TemplateAnalysis): string {
  if (template.evidence_level === "low" && template.temperature_score >= 70) {
    return `뉴스는 ${josa(template.topic, "으로", "로")} 시끄러운데, 공시로 확인된 건 거의 없어요. 기사만으로 띄우는 흐름일 수 있어요.`;
  }
  const news = `뉴스는 ${template.topic}에 쏠려 있고`;
  const disclosure =
    template.evidence_level === "high" ? "공시로도 대부분 확인돼요" : template.evidence_level === "medium" ? "공시로 확인된 건 절반쯤이에요" : "공식 확인은 아직 조금이에요";
  const community = template.change >= 0 ? "커뮤니티는 기대가 앞서요" : "커뮤니티는 조심스러워요";
  return `${news}, ${disclosure}. ${community}.`;
}
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
    { type: "news", title: `${company.company_name} ${template.topic} 관련 보도`, publisher: "Mock News", published_at: "2026-09-01T02:30:00Z", url: "https://example.com/mock-news-1", meta: { issue_count: template.evidence_level === "low" ? 4 : 2 } },
    { type: "news", title: `${company.company_name} 업종 수급 변화 분석`, publisher: "Mock Market", published_at: "2026-08-31T06:00:00Z", url: "https://example.com/mock-news-2", meta: template.evidence_level === "low" ? { issue_count: 3 } : undefined },
    { type: "news", title: `${template.topic} 기대와 가격 부담 동시 점검`, publisher: "Mock Economy", published_at: "2026-08-31T03:10:00Z", url: "https://example.com/mock-news-3", meta: template.evidence_level === "low" ? { issue_count: 3 } : undefined },
    { type: "news", title: `${company.company_name} 실적 발표 전 확인 포인트`, publisher: "Mock Securities", published_at: "2026-08-30T07:40:00Z", url: "https://example.com/mock-news-4" },
    { type: "news", title: `${company.company_name} 단기 변동성 확대 가능성`, publisher: "Mock Daily", published_at: "2026-08-30T01:20:00Z", url: "https://example.com/mock-news-5" },
  ];
}

function buildTemplateDisclosureSources(company: Company, template: TemplateAnalysis): AnalysisSource[] {
  return [
    { type: "disclosure", title: `${company.company_name} 주요사항보고서`, publisher: "Mock DART", published_at: "2026-08-29T08:00:00Z", url: "https://example.com/mock-disclosure-1", meta: template.evidence_level === "low"
        ? { receipt_no: `20260829${company.stock_code}`, confirmed: ["정기 재무 지표 제출"], unconfirmed: [`${template.topic} 관련 공식 공시`, "계약·수주 금액", "다음 분기 실적 반영 폭", "시장 기대와 실제 숫자의 차이"] }
        : { receipt_no: `20260829${company.stock_code}`, confirmed: [`${template.topic} 관련 공개 자료`, "최근 재무 지표 제출", "주요 사업 현황 공시"], unconfirmed: ["다음 분기 실적 반영 폭", "단기 가격 촉매 지속성", "시장 기대와 실제 숫자의 차이"] } },
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
      reason: partial
        ? "커뮤니티 반응을 제외하고 뉴스와 공시 중심으로 확인했어요."
        : template.evidence_level === "low"
          ? `${template.topic}은 뉴스로만 돌고 있고, 공시·보고서로 확인된 부분은 아직 적어요.`
          : template.evidence_level === "high"
            ? `${template.topic} 관련 내용이 공시·보고서로도 대부분 확인돼요.`
            : `${template.topic} 관련 공개 자료를 함께 확인했어요. 일부는 아직 기대 단계예요.`,
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
      personalized_checkpoints: composePersonal("삼성전자", "HBM 메모리", samsung.member_detail.market_temperature.score, samsung.member_detail.evidence_level.level, user),
    });
  }

  return {
    request_id: requestId(),
    status: partial ? "partial_completed" : "success",
    access_level: "member",
    requires_login: false,
    company: companyPayload(company),
    price: templatePrice(template),
    one_line_summary: composeOneLiner(template),
    detail: buildTemplateDetail(company, template, partial),
    personalized_checkpoints: composePersonal(company.company_name, template.topic, template.temperature_score, template.evidence_level, user),
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
    one_line_summary: template ? composeOneLiner(template) : "공개 데이터로 확인할 내용을 정리했어요.",
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
    personalized_checkpoints: composePersonal("삼성전자", "HBM 메모리", samsung.member_detail.market_temperature.score, samsung.member_detail.evidence_level.level, user),
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
