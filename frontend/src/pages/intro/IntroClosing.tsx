import { useRef } from "react";
import { useInView } from "motion/react";
import { Mascot } from "../../components/mascot/Mascot";
import { IntroCta } from "./IntroHero";

const MATERIALS = [["현재가", "장 마감 기준"], ["뉴스", "최근 기사, 출처 표시"], ["전자공시", "공식 자료"], ["커뮤니티 반응", "사실이 아닌 시장 반응"]];

export function IntroClosing() {
  const trust = useRef<HTMLElement>(null);
  const ending = useRef<HTMLElement>(null);
  const trustSeen = useInView(trust, { once: true, amount: 0.3 });
  const endingSeen = useInView(ending, { once: true, amount: 0.35 });
  return (
    <>
      <section ref={trust} className={`intro-trust${trustSeen ? " is-seen" : ""}`} aria-labelledby="intro-trust-title">
        <div className="intro-trust__copy">
          <h2 id="intro-trust-title"><span className="intro-strike">추천</span>도, <br className="intro-mobile" /><span className="intro-strike">목표주가</span>도<br className="intro-desktop" /> 없어요.</h2>
          <p><span className="intro-desktop">살래말래는 사라고도 팔라고도 하지 않아요. </span>결정은 직접, 확인할 재료는 저희가 챙겨요. 커뮤니티 반응은 사실이 아닌 시장 반응이라고 따로 표시해요.</p>
        </div>
        <div className="intro-materials">
          <p>한 줄에 붙는 재료</p>
          <dl>{MATERIALS.map(([title, detail]) => <div key={title}><dt>{title}</dt><dd>{detail}</dd></div>)}</dl>
        </div>
      </section>
      <section ref={ending} className={`intro-ending${endingSeen ? " is-seen" : ""}`} aria-labelledby="intro-ending-title">
        <div className="intro-ending__brand">
          <div className="intro-wordmark" aria-label="살래? 말래?">살래<span>?</span> 말래<span>?</span></div>
          <Mascot state="wink" size={120} className="intro-ending__mascot" />
        </div>
        <h2 id="intro-ending-title">궁금한 종목 하나면<br className="intro-mobile" /> 시작해요.</h2>
        <IntroCta ending />
      </section>
    </>
  );
}
