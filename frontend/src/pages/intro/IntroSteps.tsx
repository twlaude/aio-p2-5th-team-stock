import { useEffect, useRef, useState } from "react";
import { motion, useInView, useReducedMotion, useScroll, useTransform } from "motion/react";
import { INTRO_SENTENCE as SENTENCE } from "./PhoneMock";
import "./intro-steps.css";

const STEPS = [
  {
    title: "흩어진 정보를 모아요",
    desktop: "현재가, 최근 뉴스, 전자공시, 사람들의 반응까지 한곳에 모아요.",
    mobile: "현재가, 뉴스, 공시, 사람들의 반응까지 한곳에.",
  },
  {
    title: "핵심만 한 줄로 정리해요",
    desktop: "확인된 사실과 반응을 가려내고, 지금 꼭 봐야 할 것을 한 문장으로 짚어줘요.",
    mobile: "확인된 사실과 반응을 가려내서 한 문장으로.",
  },
  {
    title: "출처를 남겨요",
    desktop: "어떤 자료를 언제 봤는지, 문장 옆에 출처를 적어놨어요.",
    mobile: "어떤 자료를 언제 봤는지 출처를 적어놨어요.",
  },
];
const TAGS = ["뉴스 3건", "공시 1건", "커뮤니티 · 반응만", "09-01 15:30 기준"];
const PIECES = [
  <><small>뉴스</small><strong>AI 메모리 수요 확대에 HBM 증설 검토</strong></>,
  <>공시 · 08-29 · 정기보고서</>,
  <>커뮤니티 · 사실이 아닌 시장 반응 · 이번엔 진짜 간다던데…</>,
  <>삼성전자 78,500 <span className="intro-stage__up">+3.2%</span></>,
];
const FLY = [{ x: -110, y: -50 }, { x: 40, y: -24 }, { x: -100, y: 30 }, { x: 40, y: 60 }];
const COLLAPSE_Y = [88, 30, -28, -92];
const SPRING = { type: "spring" as const, stiffness: 270, damping: 21 };

function TypedSentence() {
  const [count, setCount] = useState(0);
  useEffect(() => {
    let timer: ReturnType<typeof setInterval>;
    const delay = setTimeout(() => {
      let next = 0;
      timer = setInterval(() => {
        next += 1;
        setCount(next);
        if (next >= SENTENCE.length) clearInterval(timer);
      }, 28);
    }, 280);
    return () => { clearTimeout(delay); clearInterval(timer); };
  }, []);
  return <span>{SENTENCE.slice(0, count)}<span className="intro-stage__cursor" hidden={count >= SENTENCE.length} /></span>;
}

function MiniStage({ step, inline = false }: { step: number; inline?: boolean }) {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: inline, amount: 0.3 });
  const reduced = useReducedMotion();
  const playing = inView && !reduced;
  return (
    <div ref={ref} className="intro-stage" data-stage={step} aria-hidden="true">
      <div className="intro-stage__header"><span>삼성전자</span><span>Mock</span></div>
      <div className="intro-stage__body" key={playing ? "play" : "rest"}>
        {(step === 1 || playing) && (
          <div className="intro-stage__pieces">
            {PIECES.map((piece, index) => (
              <motion.div
                key={index}
                className="intro-stage__piece"
                initial={playing ? (step === 1
                  ? { ...FLY[index], opacity: 0, scale: 0.92 }
                  : { x: 0, y: 0, opacity: 1, scale: 1 }) : false}
                animate={step === 1
                  ? { x: 0, y: 0, opacity: 1, scale: 1 }
                  : { x: 0, y: COLLAPSE_Y[index], opacity: 0, scale: 0.2 }}
                transition={playing ? { ...SPRING, delay: step === 1 ? index * 0.08 : 0 } : { duration: 0 }}
              >{piece}</motion.div>
            ))}
          </div>
        )}
        {step >= 2 && (
          <div className="intro-stage__summary">
            <motion.div
              className="intro-stage__bubble"
              initial={playing ? { opacity: 0, scale: 0.9 } : false}
              animate={{ opacity: 1, scale: 1 }}
              transition={playing ? { ...SPRING, damping: 16, delay: 0.24 } : { duration: 0 }}
            >
              {playing && step === 2 ? <TypedSentence /> : SENTENCE}
            </motion.div>
            {step === 3 && (
              <div className="intro-stage__tags">
                {TAGS.map((tag, index) => (
                  <motion.span key={tag}
                    initial={playing ? { opacity: 0, scale: 0.9, y: 6 } : false}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    transition={playing ? { ...SPRING, delay: 0.12 * index + 0.12 } : { duration: 0 }}
                  >{tag}</motion.span>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export function IntroSteps() {
  const rows = useRef<HTMLDivElement>(null);
  const [active, setActive] = useState(1);
  const reduced = useReducedMotion();
  const { scrollYProgress } = useScroll({ target: rows, offset: ["start center", "end center"] });
  const dashOffset = useTransform(scrollYProgress, [0, 1], [100, 0]);
  useEffect(() => {
    const elements = rows.current?.querySelectorAll<HTMLElement>("[data-step]");
    if (!elements) return;
    const observer = new IntersectionObserver((entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) setActive(Number((entry.target as HTMLElement).dataset.step));
      }
    }, { rootMargin: "-42% 0px -57% 0px", threshold: 0 });
    elements.forEach((row) => observer.observe(row));
    return () => observer.disconnect();
  }, []);
  return (
    <section className="intro-steps intro-content" aria-labelledby="intro-steps-heading">
      <p id="intro-steps-heading" className="intro-steps__eyebrow">이렇게 도와드려요</p>
      <div className="intro-steps__layout">
        <div ref={rows} className="intro-steps__rows">
          <svg className="intro-steps__progress" viewBox="0 0 2 100" preserveAspectRatio="none" aria-hidden="true">
            <path d="M1 0V100" className="intro-steps__track" />
            <motion.path d="M1 0V100" strokeDasharray="100" style={{ strokeDashoffset: reduced ? 0 : dashOffset }} />
          </svg>
          {STEPS.map((step, index) => (
            <div key={step.title} className="intro-step" data-step={index + 1} data-past={!reduced && index + 1 < active}>
              <span className="intro-step__number">0{index + 1}</span>
              <div className="intro-step__copy">
                <h2>{step.title}</h2>
                <p className="intro-step__desktop-copy">{step.desktop}</p>
                <p className="intro-step__mobile-copy">{step.mobile}</p>
              </div>
              <div className="intro-step__inline"><MiniStage step={index + 1} inline /></div>
            </div>
          ))}
        </div>
        <div className="intro-steps__sticky"><MiniStage step={reduced ? 3 : active} /></div>
      </div>
      <p className="intro-steps__sr">한 줄 설명 예시: {SENTENCE} 출처: {TAGS.join(", ")}.</p>
    </section>
  );
}
