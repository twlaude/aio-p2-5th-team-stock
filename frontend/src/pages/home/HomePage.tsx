import { ArrowRight, RefreshCw } from "lucide-react";
import type { FormEvent } from "react";
import { useEffect, useState } from "react";

import { apiClient } from "../../services/backend_api";
import type { AnalysisResponse, CompaniesResponse } from "../../services/backend_api/client";
import type { AuthSession } from "../../state/auth";
import { readPendingQuery, savePendingQuery } from "../../state/search";

interface HomePageProps {
  session: AuthSession | null;
}

export function HomePage({ session }: HomePageProps) {
  const [query, setQuery] = useState(() => readPendingQuery() ?? "삼성전자");
  const [companies, setCompanies] = useState<CompaniesResponse | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    apiClient
      .getCompanies()
      .then(setCompanies)
      .catch((cause: unknown) => setError(cause instanceof Error ? cause.message : "기업 목록을 불러오지 못했어요."));
  }, []);

  const runAnalysis = async (nextQuery = query) => {
    setLoading(true);
    setError(null);
    savePendingQuery(nextQuery);
    try {
      const response = await apiClient.createAnalysis({ query: nextQuery }, session?.token);
      setAnalysis(response);
    } catch (cause) {
      setAnalysis(null);
      setError(cause instanceof Error ? cause.message : "분석을 불러오지 못했어요.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void runAnalysis(query);
  }, [session?.token]);

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    void runAnalysis(query);
  };

  return (
    <section className="page-stack">
      <div className="page-heading">
        <div className="eyebrow">item 1 scaffold</div>
        <h1 className="page-title">목 API 계약 확인</h1>
        <p className="page-copy">홈은 기업 목록과 분석 응답 JSON을 호출해 보여줘요.</p>
      </div>

      <form className="control-row" onSubmit={handleSubmit}>
        <input
          className="text-input"
          aria-label="분석할 기업명 또는 종목코드"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="기업명 또는 종목코드"
        />
        <button className="pill-button pill-button--primary" type="submit" disabled={loading}>
          {loading ? <RefreshCw size={16} aria-hidden="true" /> : <ArrowRight size={16} aria-hidden="true" />}
          살펴보기
        </button>
      </form>

      {error ? <div className="error-copy">{error}</div> : null}

      <div className="json-grid">
        <JsonCard title="GET /api/v1/companies" value={companies} />
        <JsonCard title="POST /api/v1/analyses" value={analysis} />
        <JsonCard title="auth state" value={session} wide />
      </div>
    </section>
  );
}

interface JsonCardProps {
  title: string;
  value: unknown;
  wide?: boolean;
}

function JsonCard({ title, value, wide = false }: JsonCardProps) {
  return (
    <article className={wide ? "json-card json-card--wide" : "json-card"}>
      <h2 className="json-card__title">{title}</h2>
      <div className="json-card__body">
        <pre>{JSON.stringify(value ?? { status: "loading" }, null, 2)}</pre>
      </div>
    </article>
  );
}
