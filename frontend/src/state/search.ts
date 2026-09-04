import type { AnalysisResponse } from "../services/backend_api/client";
import type { MockScenario } from "../services/backend_api/mock";

const PENDING_QUERY_KEY = "sallae.search.pendingQuery";

export interface SearchState {
  query: string;
  pendingQuery: string | null;
  status: "idle" | "loading" | "ready" | "error";
  scenario: MockScenario;
  result: AnalysisResponse | null;
}

function getStorage() {
  return typeof window === "undefined" ? null : window.localStorage;
}

export function readPendingQuery() {
  return getStorage()?.getItem(PENDING_QUERY_KEY) ?? null;
}

export function savePendingQuery(query: string) {
  const normalized = query.trim();
  if (normalized) {
    getStorage()?.setItem(PENDING_QUERY_KEY, normalized);
  }
}

export function clearPendingQuery() {
  getStorage()?.removeItem(PENDING_QUERY_KEY);
}

export function createInitialSearchState(query = "삼성전자"): SearchState {
  return {
    query,
    pendingQuery: readPendingQuery(),
    status: "idle",
    scenario: null,
    result: null,
  };
}
