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
  const source = sources.find((item) => item.type === "community");
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
  const source = sources.find((item) => item.type === "community");
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
    .filter((source) => source.type === type)
    .slice(0, type === "news" ? 5 : 3)
    .map((source) => ({
      title: source.title,
      publisher: source.publisher,
      publishedAtLabel: publishedAtLabel(source.published_at),
      url: source.url,
      issueCount: numberMeta(source.meta, "issue_count") ?? undefined,
      receiptNo: stringMeta(source.meta, "receipt_no"),
    }));
}

export function countOf(sources: AnalysisSource[], type: SourceType) {
  return sources.filter((source) => source.type === type).length;
}

export function deriveDisclosureChecks(sources: AnalysisSource[]): DisclosureChecks {
  const checks = sources
    .filter((source) => source.type === "disclosure")
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
