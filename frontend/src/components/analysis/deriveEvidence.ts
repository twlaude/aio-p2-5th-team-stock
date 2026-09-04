import type { AnalysisSource, EvidenceLevel, SourceType } from "../../services/backend_api/client";

export interface CommunityEvidence {
  samples: number;
  positive: number;
  neutral: number;
  negative: number;
  fgi: number | null;
  topics: TopicEvidence[];
}

export interface EvidenceItem {
  title: string;
  publisher?: string;
  publishedAtLabel: string;
  url?: string;
  issueCount?: number;
  receiptNo?: string;
  disclosureKind?: "major" | "periodic";
}

export type TopicSentiment = "positive" | "neutral" | "negative";

export interface TopicEvidence {
  text: string;
  sentiment: TopicSentiment;
  weight: 1 | 2 | 3 | 4 | 5;
}

export interface DisclosureChecks {
  confirmed: string[];
  unconfirmed: string[];
}

export interface EvidenceLevelView {
  text: "많이 확인됨" | "절반쯤" | "아직 조금";
  segments: 1 | 2 | 3;
}

function numberMeta(meta: AnalysisSource["meta"], key: string) {
  const value = meta?.[key];
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function stringMeta(meta: AnalysisSource["meta"], key: string) {
  const value = meta?.[key];
  return typeof value === "string" && value.trim() ? value.trim() : undefined;
}

function disclosureKindMeta(meta: AnalysisSource["meta"]): EvidenceItem["disclosureKind"] {
  const value = meta?.disclosure_kind;
  return value === "major" || value === "periodic" ? value : undefined;
}

function stringArrayMeta(meta: AnalysisSource["meta"], key: string) {
  const value = meta?.[key];
  if (!Array.isArray(value)) {
    return [];
  }
  return value.filter((item): item is string => typeof item === "string" && item.trim().length > 0).map((item) => item.trim());
}

function isTopicSentiment(value: unknown): value is TopicSentiment {
  return value === "positive" || value === "neutral" || value === "negative";
}

function topicWeight(value: unknown): TopicEvidence["weight"] | null {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    return null;
  }
  const rounded = Math.round(value);
  if (rounded < 1 || rounded > 5) {
    return null;
  }
  return rounded as TopicEvidence["weight"];
}

export function deriveTopics(sources: AnalysisSource[]): TopicEvidence[] {
  const source = sources.find((item) => item.source_type === "community");
  const rawTopics = source?.meta?.topics;
  if (!Array.isArray(rawTopics)) {
    return [];
  }

  return rawTopics
    .map((topic): TopicEvidence | null => {
      if (!topic || typeof topic !== "object") {
        return null;
      }
      const value = topic as Record<string, unknown>;
      const text = typeof value.text === "string" ? value.text.trim() : "";
      const sentiment = value.sentiment;
      const weight = topicWeight(value.weight);
      if (!text || !isTopicSentiment(sentiment) || weight === null) {
        return null;
      }
      return { text, sentiment, weight };
    })
    .filter((topic): topic is TopicEvidence => topic !== null)
    .slice(0, 16);
}

export function deriveCommunity(sources: AnalysisSource[]): CommunityEvidence | null {
  const source = sources.find((item) => item.source_type === "community");
  if (!source?.meta) {
    return null;
  }

  const samples = numberMeta(source.meta, "samples");
  const positive = numberMeta(source.meta, "positive");
  const neutral = numberMeta(source.meta, "neutral");
  const negative = numberMeta(source.meta, "negative");
  if (samples === null || positive === null || neutral === null || negative === null) {
    return null;
  }

  return {
    samples,
    positive,
    neutral,
    negative,
    fgi: numberMeta(source.meta, "fgi"),
    topics: deriveTopics(sources),
  };
}

function pad2(value: number) {
  return String(value).padStart(2, "0");
}

export function publishedAtLabel(value?: string) {
  if (!value) {
    return "";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "";
  }

  const day = `${pad2(date.getMonth() + 1)}-${pad2(date.getDate())}`;
  if (!value.includes("T")) {
    return day;
  }

  return `${day} ${pad2(date.getHours())}:${pad2(date.getMinutes())}`;
}

export function deriveItems(sources: AnalysisSource[], type: Exclude<SourceType, "community">): EvidenceItem[] {
  return sources
    .filter((source) => source.source_type === type)
    .slice(0, type === "news" ? 5 : 3)
    .map((source) => ({
      title: source.title,
      publisher: stringMeta(source.meta, "publisher"),
      publishedAtLabel: publishedAtLabel(source.published_at),
      url: source.url,
      issueCount: numberMeta(source.meta, "issue_count") ?? undefined,
      receiptNo: stringMeta(source.meta, "receipt_number"),
      disclosureKind: disclosureKindMeta(source.meta),
    }));
}

export function countOf(sources: AnalysisSource[], type: SourceType) {
  return sources.filter((source) => source.source_type === type).length;
}

export function deriveDisclosureChecks(sources: AnalysisSource[]): DisclosureChecks {
  const checks = sources
    .filter((source) => source.source_type === "disclosure")
    .reduce<DisclosureChecks>(
      (acc, source) => ({
        confirmed: [...acc.confirmed, ...stringArrayMeta(source.meta, "confirmed")],
        unconfirmed: [...acc.unconfirmed, ...stringArrayMeta(source.meta, "unconfirmed")],
      }),
      { confirmed: [], unconfirmed: [] },
    );

  return {
    confirmed: Array.from(new Set(checks.confirmed)),
    unconfirmed: Array.from(new Set(checks.unconfirmed)),
  };
}

export function fgiLabel(fgi: number | null | undefined) {
  if (typeof fgi !== "number" || !Number.isFinite(fgi)) {
    return null;
  }
  if (fgi <= 24) {
    return "극도 공포";
  }
  if (fgi <= 44) {
    return "공포";
  }
  if (fgi <= 55) {
    return "중립";
  }
  if (fgi <= 74) {
    return "탐욕";
  }
  if (fgi <= 100) {
    return "극도 탐욕";
  }
  return null;
}

export function evidenceLevelText(level: EvidenceLevel): EvidenceLevelView {
  if (level === "high") {
    return { text: "많이 확인됨", segments: 3 };
  }
  if (level === "medium") {
    return { text: "절반쯤", segments: 2 };
  }
  return { text: "아직 조금", segments: 1 };
}

/** 분위기 vs 근거 — 시장 관심(온도)과 공식 확인(공시·보고서)의 온도차 판정. 뉴스만 띄워 주가를 부양하는 흐름을 잡기 위한 화면용 휴리스틱.
 *  실서비스에선 MCP Client의 공통 분석이 같은 판단을 계약 필드로 내려주는 게 맞다(팀 제안 예정). */
export type GapLevel = "large" | "some" | "small" | "quiet";

export interface GapSignal {
  text: string;
  tone: "warn" | "ok" | "info";
}

export interface GapCheck {
  level: GapLevel;
  heat: number; // 0~100
  confirmSegments: 1 | 2 | 3;
  verdict: string;
  advice: string;
  signals: GapSignal[];
}

export function deriveGapCheck(input: {
  temperatureScore: number;
  evidenceLevel: EvidenceLevel;
  sources: AnalysisSource[];
  changeRate: number;
}): GapCheck {
  const { temperatureScore: heat, evidenceLevel, sources, changeRate } = input;
  const confirmSegments = evidenceLevelText(evidenceLevel).segments;
  const news = sources.filter((s) => s.source_type === "news");
  const disclosures = sources.filter((s) => s.source_type === "disclosure");
  const community = deriveCommunity(sources);
  const checks = deriveDisclosureChecks(sources);
  const reprint = news.reduce((sum, s) => sum + (numberMeta(s.meta, "issue_count") ?? 1), 0);
  const reprintRatio = news.length ? reprint / news.length : 0;
  const positiveRatio = community && community.samples > 0 ? community.positive / community.samples : null;

  const signals: GapSignal[] = [];
  if (news.length >= 4) signals.push({ text: reprintRatio >= 1.8 ? `비슷한 기사가 반복돼요 (${news.length}건이 ${reprint}번 재게재)` : `뉴스 ${news.length}건이 짧은 기간에 몰렸어요`, tone: reprintRatio >= 1.8 ? "warn" : "info" });
  if (disclosures.length === 0) signals.push({ text: "이 기간 공시로 확인된 내용이 없어요", tone: "warn" });
  else if (checks.unconfirmed.length > checks.confirmed.length) signals.push({ text: `공시로 확인된 것(${checks.confirmed.length})보다 아직 아닌 것(${checks.unconfirmed.length})이 많아요`, tone: "warn" });
  else if (checks.confirmed.length > 0) signals.push({ text: `공시·보고서로 확인된 항목 ${checks.confirmed.length}개`, tone: "ok" });
  if (positiveRatio !== null && positiveRatio >= 0.6) signals.push({ text: `커뮤니티 긍정 ${Math.round(positiveRatio * 100)}% — 분위기가 앞서가요`, tone: heat >= 60 ? "warn" : "info" });
  if (changeRate >= 3) signals.push({ text: `가격이 하루 ${changeRate.toFixed(1)}% 올랐어요`, tone: "info" });

  let level: GapLevel = "small";
  // 온도 v2(평소=50, 라벨 40/60/80) 기준 — backend narrative.gap_state·mock.ts gapState와 동일하게 유지
  if (heat >= 60 && evidenceLevel === "low") level = "large";
  else if ((heat >= 60 && evidenceLevel === "medium") || (heat >= 80 && evidenceLevel !== "low")) level = "some";
  else if (heat < 45 && evidenceLevel === "high") level = "quiet";

  const copy: Record<GapLevel, { verdict: string; advice: string }> = {
    large: { verdict: "다들 환호하는데, 공식 자료로 확인된 건 거의 없어요.", advice: "기사와 커뮤니티가 앞서가는 구간이에요. 공시가 따라오는지 먼저 확인해 보세요." },
    some: { verdict: "관심은 뜨겁고, 확인된 재료는 절반쯤이에요.", advice: "확인된 부분과 기대만 있는 부분을 나눠서 보세요." },
    small: { verdict: "관심과 확인된 재료가 비슷한 온도예요.", advice: "특별히 앞서가는 신호는 없어요. 평소 기준대로 보면 돼요." },
    quiet: { verdict: "조용하지만 공식 자료는 탄탄해요.", advice: "시장 관심이 아직 낮은 구간이에요. 왜 조용한지 한 번 살펴볼 만해요." },
  };
  return { level, heat, confirmSegments, verdict: copy[level].verdict, advice: copy[level].advice, signals };
}
