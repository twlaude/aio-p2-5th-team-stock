import { useLayoutEffect, useRef } from "react";
import { IntroHero } from "./IntroHero";
import { CompanyRail } from "./CompanyRail";
import { IntroSteps } from "./IntroSteps";
import { IntroClosing } from "./IntroClosing";
import "./intro.css";

export function IntroPage() {
  const page = useRef<HTMLDivElement>(null);
  useLayoutEffect(() => {
    const shell = page.current?.closest(".app-shell");
    shell?.classList.add("intro-page");
    const update = () => shell?.classList.toggle("intro-page--scrolled", window.scrollY > 40);
    update();
    window.addEventListener("scroll", update, { passive: true });
    return () => {
      shell?.classList.remove("intro-page", "intro-page--scrolled");
      window.removeEventListener("scroll", update);
    };
  }, []);
  return (
    <div className="intro-content" ref={page}>
      <IntroHero />
      <CompanyRail />
      <IntroSteps />
      <IntroClosing />
      <footer className="intro-footer">
        <p>본 서비스는 투자 추천이 아닌 정보 제공을 목적으로 합니다.</p>
        <p>앙코르 AI 오케스트레이션 1기 · 5팀 · 소개 화면의 종목·가격·문장은 예시예요.</p>
      </footer>
    </div>
  );
}
