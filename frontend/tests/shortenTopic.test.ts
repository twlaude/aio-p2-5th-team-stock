import { describe, expect, it } from "vitest";

import { TOPIC_MAX_CHARS, shortenTopic } from "../src/components/stock/shortenTopic";

const LIVE_SAMPLES: Array<[string, string]> = [
  ["대규모 자사주 매입·소각", "대규모 자사주 매입"],
  ["높은 밸류에이션 부담", "높은 밸류에이션 부담"],
  ["배당과 주주환원 확대", "배당과 주주환원 확대"],
  ["낸드 가격 상승에 따른 실적 개선", "실적 개선"],
  ["기관·외국인 수급 유입", "기관·외국인 수급"],
  ["자사주 매입 종료 가능성", "자사주 매입 종료"],
  ["중국 메모리 업체의 추격", "중국 메모리 업체"],
  ["호재 없는 상승의 되돌림", "호재 없는 상승"],
  ["자사주 매입 종료 후 매도 압력", "매도 압력"],
  ["미국의 반도체 관세 위험", "반도체 관세 위험"],
  ["단기 차익실현과 외국인 매도 전환", "외국인 매도 전환"],
  ["솔리다임 분할상장 가능성", "솔리다임 분할상장"],
  ["무배당에 따른 주주환원 부족", "주주환원 부족"],
  ["웨스팅하우스 관련 불확실성", "불확실성"],
  ["반도체 업황 회복과 저점 매수를 기대한다.", "저점 매수"],
  ["단기 수급 변동성과 실적 확인 필요성을 우려한다.", "실적 확인 필요성"],
];

describe("shortenTopic", () => {
  it.each(LIVE_SAMPLES)("%s → %s", (input, expected) => {
    expect(shortenTopic(input)).toBe(expected);
  });

  it("짧은 주제는 그대로", () => {
    expect(shortenTopic("공매도와 매도 압력")).toBe("공매도와 매도 압력");
    expect(shortenTopic("원전 산업 확대 수혜")).toBe("원전 산업 확대 수혜");
  });

  it("어떤 입력이든 MAX 이하", () => {
    const inputs = [...LIVE_SAMPLES.map(([raw]) => raw), "아주긴한단어로만이루어진주제텍스트입니다", "a b c d e f g h i j k l m n"];
    for (const raw of inputs) expect(shortenTopic(raw).length).toBeLessThanOrEqual(TOPIC_MAX_CHARS);
  });
});
