import { EvidenceSection } from "./EvidenceSection";
import { HeroSection } from "./HeroSection";
import { PersonalSection } from "./PersonalSection";
import { ResultSection } from "./ResultSection";

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
