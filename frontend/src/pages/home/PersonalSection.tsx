import { PersonalCard } from "../../components/analysis/PersonalCard";
import { readAuthSession } from "../../state/auth";
import { useSearch } from "../../state/searchStore";
import { SiteFooter } from "./SiteFooter";
import "./personalSection.css";

export function PersonalSection() {
  const { result, status } = useSearch();
  if (status !== "ready" || !result) {
    return null;
  }
  if (result.status === "unsupported_company") {
    return null;
  }
  if (result.access_level !== "member" || !result.detail) {
    return null;
  }

  const session = readAuthSession();
  if (session?.profileCompleted === false) {
    return (
      <section id="personal" className="sallae-personal-section">
        <div className="sallae-personal-section__setup">성향 설정이 필요해요</div>
        <SiteFooter />
      </section>
    );
  }

  if (!result.personalized_checkpoints) {
    return null;
  }

  return (
    <section id="personal" className="sallae-personal-section">
      <PersonalCard checkpoints={result.personalized_checkpoints} />
      <SiteFooter />
    </section>
  );
}
