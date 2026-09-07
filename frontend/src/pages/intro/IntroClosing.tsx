import { useRef } from "react";
import { useInView } from "motion/react";
import { Mascot } from "../../components/mascot/Mascot";
import { IntroCta } from "./IntroHero";

const MATERIALS = [["현재가", "장 마감 기준"], ["뉴스", "최근 기사, 출처 표시"], ["전자공시", "공식 자료"], ["커뮤니티 반응", "투자자들의 체감 반응"]];

export function IntroClosing() {
  const trust = useRef<HTMLElement>(null);
  const ending = useRef<HTMLElement>(null);
  const trustSeen = useInView(trust, { once: true, amount: 0.3 });
  const endingSeen = useInView(ending, { once: true, amount: 0.35 });
  return (
    <>
      <section ref={trust} className={`intro-trust${trustSeen ? " is-seen" : ""}`} aria-labelledby="intro-trust-title">
        <div className="intro-trust__copy">
          <h2 id="intro-trust-title"><span className="intro-strike">정답을 찍어주는</span> 대신,<br /> 판단할 재료를 드려요.</h2>
          <p>살지 말지는 결국 스스로 정하는 일이니까요. 그 결정이 감이 아니라 근거에서 나오도록, 봐야 할 것들을 한자리에 모아 드려요.<span className="intro-desktop"> 사실은 사실대로, 반응은 반응대로.</span></p>
        </div>
        <div className="intro-materials">
          <p>한 줄을 만드는 재료들</p>
          <dl>{MATERIALS.map(([title, detail]) => <div key={title}><dt>{title}</dt><dd>{detail}</dd></div>)}</dl>
        </div>
      </section>
      <section ref={ending} className={`intro-ending${endingSeen ? " is-seen" : ""}`} aria-labelledby="intro-ending-title">
        <div className="intro-ending__brand">
          <div className="intro-wordmark" aria-label="살래? 말래?">살래<span>?</span> 말래<span>?</span></div>
          <Mascot state="wink" size={120} className="intro-ending__mascot" />
        </div>
        <h2 id="intro-ending-title">끌리는 그 종목,<br className="intro-mobile" /> 왜 끌리는지부터 볼까요?</h2>
        <IntroCta ending />
      </section>
    </>
  );
}
