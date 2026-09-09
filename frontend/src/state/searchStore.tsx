import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";

import { apiClient } from "../services/backend_api";
import type { AnalysisResponse } from "../services/backend_api/client";
import { clearPendingQuery, readPendingQuery, savePendingQuery } from "./search";

/** 모든 섹션이 공유하는 검색 상태. */
export type SearchStatus = "idle" | "loading" | "ready" | "error";

export interface SearchStore {
  /** 검색창에 적힌 값 */
  query: string;
  /** 마지막으로 분석을 요청한 값 */
  submittedQuery: string | null;
  status: SearchStatus;
  result: AnalysisResponse | null;
  error: string | null;
  /** 같은 세션에서 몇 번째 분석인지 — 재등장 애니메이션 키로 사용 */
  runId: number;
  setQuery: (query: string) => void;
  submit: (query?: string) => Promise<void>;
  retry: () => Promise<void>;
  reset: () => void;
}

const SearchContext = createContext<SearchStore | null>(null);

interface SearchProviderProps {
  token: string | undefined;
  /** 사용자가 직접 로그아웃한 시각. 바뀌면 결과를 비우고 초기 화면으로 돌아간다 (토큰 만료 자가치유와 구분). */
  logoutAt?: number;
  children: ReactNode;
}

export function SearchProvider({ token, logoutAt = 0, children }: SearchProviderProps) {
  const [query, setQuery] = useState("");
  const [submittedQuery, setSubmittedQuery] = useState<string | null>(null);
  const [status, setStatus] = useState<SearchStatus>("idle");
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [runId, setRunId] = useState(0);
  const requestSeq = useRef(0);
  const tokenRef = useRef(token);
  tokenRef.current = token;

  const submit = useCallback(async (nextQuery?: string) => {
    const target = (nextQuery ?? query).trim();
    if (!target) {
      return;
    }
    const seq = ++requestSeq.current;
    setQuery(target);
    setSubmittedQuery(target);
    setStatus("loading");
    setError(null);
    savePendingQuery(target);
    try {
      const response = await apiClient.createAnalysis({ query: target }, tokenRef.current);
      if (seq !== requestSeq.current) {
        return;
      }
      setResult(response);
      setStatus("ready");
      setRunId((id) => id + 1);
    } catch (cause) {
      if (seq !== requestSeq.current) {
        return;
      }
      setResult(null);
      setError(cause instanceof Error ? cause.message : "분석을 불러오지 못했어요.");
      setStatus("error");
    }
  }, [query]);

  const retry = useCallback(async () => {
    if (submittedQuery) {
      await submit(submittedQuery);
    }
  }, [submit, submittedQuery]);

  const reset = useCallback(() => {
    requestSeq.current += 1;
    setSubmittedQuery(null);
    setResult(null);
    setError(null);
    setStatus("idle");
    clearPendingQuery();
  }, []);

  // 토큰 변화 시: 로그인(또는 만료 자가치유로 토큰이 사라진 경우)은 보류 종목을 자동 재분석해 원래 화면으로 복귀.
  // 사용자가 직접 로그아웃한 경우(logoutAt 갱신)는 결과를 비우고 초기 화면으로 돌아간다.
  const previousToken = useRef(token);
  const previousLogoutAt = useRef(logoutAt);
  useEffect(() => {
    if (previousToken.current === token) {
      return;
    }
    previousToken.current = token;
    if (!token && logoutAt !== previousLogoutAt.current) {
      previousLogoutAt.current = logoutAt;
      reset();
      setQuery("");
      return;
    }
    const pending = submittedQuery ?? readPendingQuery();
    if (pending) {
      void submit(pending);
    }
  }, [token, logoutAt, submit, reset, submittedQuery]);

  const value = useMemo<SearchStore>(
    () => ({ query, submittedQuery, status, result, error, runId, setQuery, submit, retry, reset }),
    [query, submittedQuery, status, result, error, runId, submit, retry, reset],
  );

  return <SearchContext.Provider value={value}>{children}</SearchContext.Provider>;
}

export function useSearch(): SearchStore {
  const store = useContext(SearchContext);
  if (!store) {
    throw new Error("useSearch는 SearchProvider 안에서만 쓸 수 있어요.");
  }
  return store;
}
