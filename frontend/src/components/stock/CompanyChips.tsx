import { useState } from "react";

import companiesFixture from "../../mocks/companies.json";
import type { Company } from "../../services/backend_api/client";
import { CompaniesSheet } from "./CompaniesSheet";
import "./searchBar.css";

const companies = companiesFixture as Company[];
const popularCompanies = ["삼성전자", "SK하이닉스", "현대차", "셀트리온"];

interface CompanyChipsProps {
  onSelectCompany: (name: string) => void;
}

export function CompanyChips({ onSelectCompany }: CompanyChipsProps) {
  const [sheetOpen, setSheetOpen] = useState(false);

  return (
    <>
      <div className="company-chips" aria-label="인기 검색 기업">
        {popularCompanies.map((name) => (
          <button className="company-chip" key={name} type="button" onClick={() => onSelectCompany(name)}>
            {name}
          </button>
        ))}
        <button className="company-chip company-chip--sheet" type="button" onClick={() => setSheetOpen(true)}>
          지원 20종목 보기
        </button>
      </div>
      <CompaniesSheet
        companies={companies}
        open={sheetOpen}
        onClose={() => setSheetOpen(false)}
        onSelect={(company) => onSelectCompany(company.company_name)}
      />
    </>
  );
}
