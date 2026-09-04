import { EvidenceSection } from "./EvidenceSection";
import { HeroSection } from "./HeroSection";
import { PersonalSection } from "./PersonalSection";
import { ResultSection } from "./ResultSection";

/** 한 페이지 조립. 공유 기반 — 섹션 순서/조립만 담당, 각 섹션 파일은 영역별 소유. */
export function HomePage() {
  return (
    <>
      <HeroSection />
      <ResultSection />
      <EvidenceSection />
      <PersonalSection />
    </>
  );
}
