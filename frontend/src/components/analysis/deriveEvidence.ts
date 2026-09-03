import type { AnalysisSource, EvidenceLevel, SourceType } from "../../services/backend_api/client";

export interface CommunityEvidence {
  samples: number;
  positive: number;
  neutral: number;
  negative: number;
  fgi: number | null;
}

export interface EvidenceItem {
  title: string;
  publisher?: string;
  publishedAtLabel: string;
}

export interface EvidenceLevelView {
  text: "충분" | "보통" | "부족";
  segments: 1 | 2 | 3;
}

function numberMeta(meta: AnalysisSource["meta"], key: string) {
  const value = meta?.[key];
  return typeof value === "number" && Number.isFinite(value) ? value : null;
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
    .slice(0, 3)
    .map((source) => ({
      title: source.title,
      publisher: source.publisher,
      publishedAtLabel: publishedAtLabel(source.published_at),
    }));
}

export function countOf(sources: AnalysisSource[], type: SourceType) {
  return sources.filter((source) => source.type === type).length;
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
    return { text: "충분", segments: 3 };
  }
  if (level === "medium") {
    return { text: "보통", segments: 2 };
  }
  return { text: "부족", segments: 1 };
}
