import supported from "../../../../shared/supported_companies.json";

export function CompanyRail() {
  return (
    <section className="intro-rail" aria-label="살펴볼 수 있는 종목">
      <p>지금 살펴볼 수 있는 {supported.companies.length}종목</p>
      <div className="intro-rail__viewport" tabIndex={0} role="region" aria-label="지원 종목 이름과 코드">
        <div className="intro-rail__track">
          {[0, 1].map((copy) => (
            <ul className="intro-rail__group" key={copy} aria-hidden={copy === 1 ? true : undefined}>
              {supported.companies.map((company) => <li key={company.stock_code}><span>{company.company_name}</span><code>{company.stock_code}</code></li>)}
            </ul>
          ))}
        </div>
      </div>
    </section>
  );
}
