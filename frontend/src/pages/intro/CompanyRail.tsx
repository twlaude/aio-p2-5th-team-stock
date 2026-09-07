import { useNavigate } from "react-router-dom";
import supported from "../../../../shared/supported_companies.json";
import { useSearch } from "../../state/searchStore";

export function CompanyRail() {
  const navigate = useNavigate();
  const search = useSearch();
  // 종목을 누르면 로그인 없이 바로 그 종목의 한 줄 결론으로 — 검색창에 치고 살펴보기 누른 것과 같은 경로
  const open = (companyName: string) => {
    void search.submit(companyName);
    navigate("/");
  };
  return (
    <section className="intro-rail" aria-label="살펴볼 수 있는 종목">
      <p>지금 살펴볼 수 있는 {supported.companies.length}종목 · 누르면 로그인 없이 바로 볼 수 있어요</p>
      <div className="intro-rail__viewport" tabIndex={0} role="region" aria-label="지원 종목 이름과 코드">
        <div className="intro-rail__track">
          {[0, 1].map((copy) => (
            <ul className="intro-rail__group" key={copy} aria-hidden={copy === 1 ? true : undefined}>
              {supported.companies.map((company) => (
                <li key={company.stock_code}>
                  <button className="intro-rail__item" type="button" tabIndex={copy === 1 ? -1 : undefined} onClick={() => open(company.company_name)} aria-label={`${company.company_name} 살펴보기`}>
                    <span>{company.company_name}</span><code>{company.stock_code}</code>
                  </button>
                </li>
              ))}
            </ul>
          ))}
        </div>
      </div>
    </section>
  );
}
