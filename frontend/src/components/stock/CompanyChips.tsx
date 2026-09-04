import { useState } from "react";

import companiesFixture from "../../mocks/companies.json";
import { apiClient } from "../../services/backend_api";
import type { Company } from "../../services/backend_api/client";
import { CompaniesSheet } from "./CompaniesSheet";
import "./searchBar.css";

const fallbackCompanies = companiesFixture as Company[];
const popularCompanies = ["삼성전자", "SK하이닉스", "현대차", "셀트리온"];

interface CompanyChipsProps {
  onSelectCompany: (name: string) => void;
  onError?: (message: string) => void;
}

export function CompanyChips({ onSelectCompany, onError }: CompanyChipsProps) {
  const [sheetOpen, setSheetOpen] = useState(false);
  const [companies, setCompanies] = useState<Company[]>(fallbackCompanies);

  const openSheet = async () => {
    setSheetOpen(true);
    try {
      const response = await apiClient.getCompanies();
      setCompanies(response.companies);
    } catch (cause) {
      setSheetOpen(false);
      const message = cause instanceof Error ? cause.message : "지원 기업 목록을 불러오지 못했어요.";
      onError?.(`지원 기업 목록을 불러오지 못했어요. ${message}`);
    }
  };

  return (
    <>
      <div className="company-chips" aria-label="인기 검색 기업">
        {popularCompanies.map((name) => (
          <button className="company-chip" key={name} type="button" onClick={() => onSelectCompany(name)}>
            {name}
          </button>
        ))}
        <button className="company-chip company-chip--sheet" type="button" onClick={openSheet}>
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
