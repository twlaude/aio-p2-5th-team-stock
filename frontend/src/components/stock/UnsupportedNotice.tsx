import companiesFixture from "../../mocks/companies.json";
import type { Company } from "../../services/backend_api/client";
import { Mascot } from "../mascot/Mascot";
import { CompanyGridItem } from "./CompaniesSheet";
import "./companiesSheet.css";
import "./notice.css";

const companies = companiesFixture as Company[];
const fallbackDescription = "지금은 2026년 9월 1일 기준 코스피 시가총액 상위 20개 기업만 지원해요.";

interface UnsupportedNoticeProps {
  query: string | null;
  message?: string;
  onSelectCompany: (name: string) => void;
}

export function UnsupportedNotice({ query, message, onSelectCompany }: UnsupportedNoticeProps) {
  const displayQuery = query?.trim() || "입력한 기업";

  // motion 4b-15
  return (
    <section className="notice-stage notice-stage--unsupported">
      <div className="unsupported-notice" role="alert">
        <Mascot state="oops" size={64} />
        <div className="unsupported-notice__text">
          <h2>아직 {displayQuery} 분석은 제공하지 않아요</h2>
          <p>{message || fallbackDescription}</p>
        </div>
      </div>
      <h3 className="notice-stage__label">지원 기업 20개</h3>
      <div className="company-grid company-grid--notice">
        {companies.map((company, index) => (
          <CompanyGridItem
            company={company}
            index={index}
            key={company.stock_code}
            onSelect={(selected) => onSelectCompany(selected.company_name)}
          />
        ))}
      </div>
    </section>
  );
}
