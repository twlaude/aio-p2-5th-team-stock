import { motion, useReducedMotion, useScroll, useTransform } from "motion/react";
import { useNavigate } from "react-router-dom";
import { Mascot } from "../../components/mascot/Mascot";
import { PhoneMock } from "./PhoneMock";

export function IntroCta({ ending = false }: { ending?: boolean }) {
  const navigate = useNavigate();
  return (
    <div className={`intro-action${ending ? " intro-action--ending" : ""}`}>
      <button className="intro-cta" type="button" onClick={() => navigate("/")}>종목 살펴보기</button>
      <p className="intro-caption">로그인 없이 바로 볼 수 있어요</p>
    </div>
  );
}

export function IntroHero() {
  const reduced = useReducedMotion();
  const { scrollY } = useScroll();
  const blobY = useTransform(scrollY, [0, 900], [0, 270]);
  const blobOpacity = useTransform(scrollY, [0, 650], [1, 0]);
  const phoneY = useTransform(scrollY, [0, 900], [0, 135]);
  return (
    <section className="intro-hero" aria-labelledby="intro-title">
      <motion.div className="intro-blobs" aria-hidden="true" style={reduced ? undefined : { y: blobY, opacity: blobOpacity }}>
        <i /><i /><i />
      </motion.div>
      <div className="intro-hero__copy">
        <h1 id="intro-title"><span>살까 말까 <br className="intro-mobile" />고민될 때,</span><span>한 줄부터 <br className="intro-mobile" />읽어봐요.</span></h1>
        <p className="intro-hero__sub">뉴스·공시·시장 반응을 한 흐름으로 모아, 지금 확인할 것을 쉬운 말로 설명해요.</p>
        <IntroCta />
      </div>
      <div className="intro-hero__scene">
        <Mascot state="idle" size={150} className="intro-hero__mascot" />
        <motion.div className="intro-hero__phone" style={reduced ? undefined : { y: phoneY }}>
          <div className="intro-phone-float"><PhoneMock /></div>
        </motion.div>
      </div>
    </section>
  );
}
