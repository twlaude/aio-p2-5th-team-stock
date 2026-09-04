import { X } from "lucide-react";
import { useEffect, type MouseEvent } from "react";

import type { Company } from "../../services/backend_api/client";
import "./companiesSheet.css";

interface CompaniesSheetProps {
  open: boolean;
  companies: Company[];
  onClose: () => void;
  onSelect: (company: Company) => void;
}

interface CompanyGridItemProps {
  company: Company;
  index: number;
  onSelect: (company: Company) => void;
}

export function CompanyGridItem({ company, index, onSelect }: CompanyGridItemProps) {
  return (
    <button
      className="company-grid__item"
      type="button"
      style={{ animationDelay: `${index * 30}ms` }}
      onClick={() => onSelect(company)}
      aria-label={`${company.company_name} 검색`}
    >
      <span className="company-grid__rank">{company.rank}</span>
      <span className="company-grid__name">{company.company_name}</span>
      <span className="company-grid__code">{company.stock_code}</span>
    </button>
  );
}

export function CompaniesSheet({ open, companies, onClose, onSelect }: CompaniesSheetProps) {
  useEffect(() => {
    if (!open) {
      return undefined;
    }

    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    };

    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [onClose, open]);

  if (!open) {
    return null;
  }

  const closeFromBackdrop = (event: MouseEvent<HTMLDivElement>) => {
    if (event.target === event.currentTarget) {
      onClose();
    }
  };

  const select = (company: Company) => {
    onClose();
    onSelect(company);
  };

  return (
    <div className="companies-sheet" onMouseDown={closeFromBackdrop}>
      <section className="companies-sheet__panel" role="dialog" aria-modal="true" aria-labelledby="companies-sheet-title">
        <div className="companies-sheet__header">
          <h2 id="companies-sheet-title">지원 기업 20개</h2>
          <button className="companies-sheet__close" type="button" onClick={onClose} aria-label="지원 기업 목록 닫기">
            <X size={20} aria-hidden="true" />
          </button>
        </div>
        <div className="company-grid company-grid--sheet">
          {companies.map((company, index) => (
            <CompanyGridItem company={company} index={index} key={company.stock_code} onSelect={select} />
          ))}
        </div>
      </section>
    </div>
  );
}
