import type { FormEvent } from "react";

import { Mascot } from "../../components/mascot/Mascot";
import { useSearch } from "../../state/searchStore";

/** 영역 A 소유 — 검색 히어로(마스코트·검색바·칩·20종목 시트·로딩·미지원·에러). 아래는 스텁. */
export function HeroSection() {
  const search = useSearch();
  const onSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    void search.submit();
  };
  return (
    <section className="hero">
      <Mascot state={search.status === "loading" ? "thinking" : "idle"} />
      <h1>요즘 어떤 종목이<br />궁금하세요?</h1>
      <form onSubmit={onSubmit}>
        <input aria-label="기업명 또는 종목코드" value={search.query} onChange={(e) => search.setQuery(e.target.value)} placeholder="기업명 또는 종목코드 6자리" />
        <button type="submit" disabled={search.status === "loading"}>살펴보기</button>
      </form>
      {search.status === "loading" ? <p>모으는 중…</p> : null}
      {search.status === "error" ? <p role="alert">{search.error}</p> : null}
      {search.result?.status === "unsupported_company" ? <p role="alert">{search.result.message}</p> : null}
    </section>
  );
}
