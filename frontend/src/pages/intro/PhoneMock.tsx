export const INTRO_SENTENCE = "관심은 뜨겁지만, 공식적으로 확인된 재료는 조금 더 살펴봐야 해요.";

export function PhoneMock() {
  return (
    <div className="intro-phone" role="img" aria-label={`Mock 화면. 삼성전자 78,500원, +3.2%. ${INTRO_SENTENCE}`}>
      <div className="intro-phone__brand" aria-hidden="true">
        <b>살래<span>?</span> 말래<span>?</span></b><small>Mock</small>
      </div>
      <div className="intro-phone__price" aria-hidden="true">
        <small>005930 · KOSPI</small><strong>삼성전자</strong>
        <div><b>78,500<small>원</small></b><em>+3.2%</em></div>
      </div>
      <svg className="intro-phone__chart" viewBox="0 0 220 56" fill="none" aria-hidden="true">
        <path d="M2 40 L30 36 L58 38 L86 28 L114 30 L142 22 L170 24 L198 14 L218 10" />
        <circle cx="218" cy="10" r="3.5" />
      </svg>
      <div className="intro-phone__verdict" aria-hidden="true">
        <span>우리는 지금 이렇게 보고 있어요!</span>
        <p>{INTRO_SENTENCE}</p>
        <b>어떤 근거로 봤나요?</b>
      </div>
    </div>
  );
}
