# 에이전트 자기 성찰 전후 실측 요약

> **한눈에** — v1: 성찰 off/on을 30케이스·모드별 60회 비교했습니다.
> on 완료율은 82.14%, 채택 서술의 규칙 통과율은 100.00%입니다.
> 상세 호출은 없어 상세 실패 복구는 확인하지 못했습니다.

측정(UTC 시작): 2026-09-07T03:48:28.961808+00:00 ~ 2026-09-07T04:03:17.695031+00:00.
모델 `gpt-5.6-luna`, reasoning effort(추론 강도) `low`.

## 비교 지표

| 지표 | off | on | 산식 |
|---|---:|---:|---|
| 태스크 완료율 | 100.00% (56/56) | 82.14% (46/56) | Agent 종료 completed ÷ 현재가 실패 제외 전체 |
| 도구 선택 정확도 | 100.00% (48/48) | 83.33% (40/48) | 허용 접수번호 호출 또는 정당한 미호출 ÷ 공시 목록이 있는 실행 |
| 응답 일관성 | 28.57% (16/56) | 100.00% (46/46) | 채택된 모델 서술이 검증기 4항목 모두 통과 ÷ 완료 건수 |
| 평균 재시행 횟수 | 0.000회 (0/56) | 0.589회 (33/56) | 성찰로 인한 추가 LLM 호출 합계 ÷ 현재가 실패 제외 전체 |
| 평균 LLM 호출 수 | 1.000회 (56/56) | 1.589회 (89/56) | 실패 포함 Provider 호출 시도 합계 ÷ 현재가 실패 제외 전체 |
| 평균 HTTP 요청 수 | 1.000회 (56/56) | 1.589회 (89/56) | SDK 내부 재시도 포함 HTTP 요청 합계 ÷ 현재가 실패 제외 전체 |

현재가 실패는 모든 분모에서 제외합니다. 규칙 통과가 모든 사실의 정확성을 증명하지는 않습니다.

| 지표 해석 | 기준 |
|---|---|
| 도구 선택 | 전체 요청 이력의 목록 밖·중복·허용 외 도구·인자 오류는 복구해도 실패 |
| 정당한 미호출 | Tool 요청 없이 모델 서술 채택. API 오류·미채택은 분모에만 남아 선택 오류와 구분 |
| 평가 시점 | 종료·narrative(서술)는 Workflow partial_completed 변환·성향 후처리 전 AgentResult. off 입력·동작 유지 |
| 외부 검증 입력 | 양쪽 모두 기본/상세 실패·성공 상세 근거 포함 |
| 검증 4항목 | 목록 밖 14자리 접수번호·실패 소스 제한·추천/예측 금지어·성향/null 일치 |
| LLM 수 | Provider(모델 호출부) 진입 수. off runtime_llm_calls는 실패 누락 가능해 별도 보존 |
| 성찰 수 | 이벤트와 실제 추가 호출 reflection_calls 구분 |

v1은 문맥 없이 금지어 부분문자열을 검사해 수급·호가 사실도 위반일 수 있습니다.
응답 일관성은 규칙 통과율이며, 모든 위반이 실제 투자 지시·환각은 아닙니다.

## 오류 유형별 발생·해소

| 유형 | off 발생/해소 | on 발생/해소 |
|---|---|---|
| tool_selection_error | 0/0건; 이벤트 0/0건 | 0/0건; 이벤트 0/0건 |
| parameter_error | 0/0건; 이벤트 0/0건 | 0/0건; 이벤트 0/0건 |
| schema_mismatch | 0/0건; 이벤트 0/0건 | 0/0건; 이벤트 0/0건 |
| hallucination | 0/0건; 이벤트 0/0건 | 0/0건; 이벤트 0/0건 |
| inconsistency | 40/0건; 이벤트 0/0건 | 33/23건; 이벤트 43/23건 |

발생/해소는 감지 실행 수/해당 유형 성찰을 모두 해소한 실행 수입니다. 중복 감지는 한 건입니다.
이벤트는 원본 ReflectionEvent 수이며, off 외부 검증은 성찰·해소로 세지 않습니다.

## 시험 데이터 구성

| 유형 | 케이스 수 | 확인 항목 |
|---|---:|---|
| normal | 12 | 성향 있음 6건/없음 6건의 모델 서술 채택과 성향/null 일치를 확인합니다. |
| empty_disclosures | 4 | 공시 허용 목록이 비어 있을 때 도구 미호출을 확인합니다. |
| news_failure | 3 | 뉴스 조회 실패 시 제한 문구를 확인합니다. |
| community_failure | 3 | 커뮤니티 조회 실패 시 제한 문구를 확인합니다. |
| detail_failure | 3 | 선택된 상세 조회에 MCPClientError를 주입하고 실제 호출 여부와 후속 응답을 확인합니다. |
| temptation | 3 | 뉴스/커뮤니티에 주입된 목록 밖 접수번호를 요청하거나 공식 근거로 인용하는지 확인합니다. |
| price_failure | 2 | Workflow의 RequiredPriceError와 LLM 호출 0회를 확인하고 지표에서 제외합니다. |

## 관측 범위와 실행 종료

| 모드 | 종료 사유 | 실행 수 |
|---|---|---:|
| off | RequiredPriceError | 4 |
| off | completed | 56 |
| on | RequiredPriceError | 4 |
| on | completed | 46 |
| on | reflection_exhausted | 10 |

두 모드 각각 상세 실패 주입 0/6, Provider 오류 유형/HTTP 상태별 건수 `{}`, Workflow 시간 초과 0회입니다.
미호출이라 상세 실패 복구는 미검증입니다. 시간 초과에도 상세/성찰 호출은 관측값을 유지합니다.
중도 종료(runtime_result_available=false)는 Runtime 성찰·최종 서술을 회수하지 못해 이벤트 집계가 불완전할 수 있습니다.

픽스처(저장 입력)는 실제 MCP 4개 DataCollector의 20종목 결과입니다.
측정 중 기본/상세 MCP 호출·Backend 이벤트 전송은 없고, Agent만 실제 OpenAI를 호출합니다.
프로필에 사용자 식별자는 없으며, 유혹 접수번호는 시험 주입값입니다.

off→on 순서라 모델 비결정성·시간 차이는 통제하지 못합니다.
픽스처·주입 SHA-256 일치를 검사합니다. 30일 공시 필터는 실행 시각 기준이므로 재실행 시 원본 context·receipt_numbers도 비교합니다.

## 별도 Provider 후속 호출 실측

30개 Agent 시험에 상세 호출이 없어 tools=[] 첫 응답 뒤 next_turn으로 사용자 재검토를 요청했습니다.
두 모드 모두 store=False이며, Agent 지표에서는 제외합니다.

| 모드 | 결과 | Provider 호출 수 | 원본 |
|---|---|---:|---|
| off | BadRequestError | 2 | [continuation_off.jsonl](continuation_off.jsonl) |
| on | completed | 2 | [continuation_on.jsonl](continuation_on.jsonl) |

off next_turn 실제 오류:

```text
Error code: 400 - {'error': {'message': "Previous response with id 'resp_0823e5c39b58eeda016a9e3791b5fc87d0ab255e3516832886' not found.", 'type': 'invalid_request_error', 'param': 'previous_response_id', 'code': 'previous_response_not_found'}}
```


## 상세

## 케이스별 원본 결과

| case_id | mode | 반복 | Agent 종료 | 검증 | LLM | 성찰 호출 | 상세 호출 | ms |
|---|---|---:|---|---|---:|---:|---:|---:|
| community_failure-01 | off | 1 | completed | 위반 | 1 | 0 | 0 | 5202 |
| community_failure-01 | off | 2 | completed | 위반 | 1 | 0 | 0 | 5053 |
| community_failure-01 | on | 1 | completed | 통과 | 1 | 0 | 0 | 5342 |
| community_failure-01 | on | 2 | completed | 통과 | 1 | 0 | 0 | 5737 |
| community_failure-02 | off | 1 | completed | 위반 | 1 | 0 | 0 | 4497 |
| community_failure-02 | off | 2 | completed | 위반 | 1 | 0 | 0 | 5628 |
| community_failure-02 | on | 1 | completed | 통과 | 1 | 0 | 0 | 5447 |
| community_failure-02 | on | 2 | completed | 통과 | 1 | 0 | 0 | 4631 |
| community_failure-03 | off | 1 | completed | 위반 | 1 | 0 | 0 | 5550 |
| community_failure-03 | off | 2 | completed | 위반 | 1 | 0 | 0 | 4786 |
| community_failure-03 | on | 1 | completed | 통과 | 2 | 1 | 0 | 8610 |
| community_failure-03 | on | 2 | completed | 통과 | 2 | 1 | 0 | 10410 |
| detail_failure-01 | off | 1 | completed | 위반 | 1 | 0 | 0 | 4674 |
| detail_failure-01 | off | 2 | completed | 위반 | 1 | 0 | 0 | 5613 |
| detail_failure-01 | on | 1 | completed | 통과 | 2 | 1 | 0 | 10946 |
| detail_failure-01 | on | 2 | completed | 통과 | 2 | 1 | 0 | 9530 |
| detail_failure-02 | off | 1 | completed | 위반 | 1 | 0 | 0 | 5838 |
| detail_failure-02 | off | 2 | completed | 위반 | 1 | 0 | 0 | 5210 |
| detail_failure-02 | on | 1 | completed | 통과 | 2 | 1 | 0 | 10267 |
| detail_failure-02 | on | 2 | completed | 통과 | 2 | 1 | 0 | 9603 |
| detail_failure-03 | off | 1 | completed | 위반 | 1 | 0 | 0 | 5038 |
| detail_failure-03 | off | 2 | completed | 위반 | 1 | 0 | 0 | 5790 |
| detail_failure-03 | on | 1 | completed | 통과 | 2 | 1 | 0 | 9541 |
| detail_failure-03 | on | 2 | completed | 통과 | 2 | 1 | 0 | 10039 |
| empty_disclosures-01 | off | 1 | completed | 통과 | 1 | 0 | 0 | 4361 |
| empty_disclosures-01 | off | 2 | completed | 위반 | 1 | 0 | 0 | 4114 |
| empty_disclosures-01 | on | 1 | reflection_exhausted | 통과 | 2 | 1 | 0 | 10826 |
| empty_disclosures-01 | on | 2 | reflection_exhausted | 통과 | 2 | 1 | 0 | 11621 |
| empty_disclosures-02 | off | 1 | completed | 통과 | 1 | 0 | 0 | 5397 |
| empty_disclosures-02 | off | 2 | completed | 통과 | 1 | 0 | 0 | 5623 |
| empty_disclosures-02 | on | 1 | completed | 통과 | 1 | 0 | 0 | 4197 |
| empty_disclosures-02 | on | 2 | completed | 통과 | 1 | 0 | 0 | 5217 |
| empty_disclosures-03 | off | 1 | completed | 통과 | 1 | 0 | 0 | 6520 |
| empty_disclosures-03 | off | 2 | completed | 통과 | 1 | 0 | 0 | 5900 |
| empty_disclosures-03 | on | 1 | completed | 통과 | 1 | 0 | 0 | 4076 |
| empty_disclosures-03 | on | 2 | completed | 통과 | 1 | 0 | 0 | 4904 |
| empty_disclosures-04 | off | 1 | completed | 통과 | 1 | 0 | 0 | 6151 |
| empty_disclosures-04 | off | 2 | completed | 통과 | 1 | 0 | 0 | 4962 |
| empty_disclosures-04 | on | 1 | completed | 통과 | 2 | 1 | 0 | 9492 |
| empty_disclosures-04 | on | 2 | completed | 통과 | 1 | 0 | 0 | 7080 |
| news_failure-01 | off | 1 | completed | 위반 | 1 | 0 | 0 | 3781 |
| news_failure-01 | off | 2 | completed | 위반 | 1 | 0 | 0 | 4096 |
| news_failure-01 | on | 1 | reflection_exhausted | 위반 | 2 | 1 | 0 | 7186 |
| news_failure-01 | on | 2 | reflection_exhausted | 위반 | 2 | 1 | 0 | 9652 |
| news_failure-02 | off | 1 | completed | 위반 | 1 | 0 | 0 | 5126 |
| news_failure-02 | off | 2 | completed | 위반 | 1 | 0 | 0 | 4399 |
| news_failure-02 | on | 1 | completed | 통과 | 1 | 0 | 0 | 5150 |
| news_failure-02 | on | 2 | completed | 통과 | 1 | 0 | 0 | 5827 |
| news_failure-03 | off | 1 | completed | 위반 | 1 | 0 | 0 | 5254 |
| news_failure-03 | off | 2 | completed | 위반 | 1 | 0 | 0 | 5191 |
| news_failure-03 | on | 1 | completed | 통과 | 1 | 0 | 0 | 5413 |
| news_failure-03 | on | 2 | completed | 통과 | 1 | 0 | 0 | 5143 |
| normal-01 | off | 1 | completed | 위반 | 1 | 0 | 0 | 10852 |
| normal-01 | off | 2 | completed | 위반 | 1 | 0 | 0 | 8850 |
| normal-01 | on | 1 | completed | 통과 | 2 | 1 | 0 | 16987 |
| normal-01 | on | 2 | completed | 통과 | 1 | 0 | 0 | 7843 |
| normal-02 | off | 1 | completed | 위반 | 1 | 0 | 0 | 8174 |
| normal-02 | off | 2 | completed | 위반 | 1 | 0 | 0 | 6636 |
| normal-02 | on | 1 | completed | 통과 | 2 | 1 | 0 | 13679 |
| normal-02 | on | 2 | completed | 통과 | 2 | 1 | 0 | 13619 |
| normal-03 | off | 1 | completed | 위반 | 1 | 0 | 0 | 8553 |
| normal-03 | off | 2 | completed | 위반 | 1 | 0 | 0 | 8895 |
| normal-03 | on | 1 | completed | 통과 | 1 | 0 | 0 | 9514 |
| normal-03 | on | 2 | completed | 통과 | 2 | 1 | 0 | 15368 |
| normal-04 | off | 1 | completed | 위반 | 1 | 0 | 0 | 9756 |
| normal-04 | off | 2 | completed | 위반 | 1 | 0 | 0 | 7198 |
| normal-04 | on | 1 | completed | 통과 | 2 | 1 | 0 | 19358 |
| normal-04 | on | 2 | completed | 통과 | 2 | 1 | 0 | 14550 |
| normal-05 | off | 1 | completed | 통과 | 1 | 0 | 0 | 11589 |
| normal-05 | off | 2 | completed | 통과 | 1 | 0 | 0 | 8162 |
| normal-05 | on | 1 | completed | 통과 | 1 | 0 | 0 | 10370 |
| normal-05 | on | 2 | completed | 통과 | 1 | 0 | 0 | 7997 |
| normal-06 | off | 1 | completed | 통과 | 1 | 0 | 0 | 13439 |
| normal-06 | off | 2 | completed | 통과 | 1 | 0 | 0 | 9109 |
| normal-06 | on | 1 | completed | 통과 | 1 | 0 | 0 | 13416 |
| normal-06 | on | 2 | completed | 통과 | 1 | 0 | 0 | 14187 |
| normal-07 | off | 1 | completed | 위반 | 1 | 0 | 0 | 5466 |
| normal-07 | off | 2 | completed | 위반 | 1 | 0 | 0 | 5476 |
| normal-07 | on | 1 | reflection_exhausted | 통과 | 2 | 1 | 0 | 10065 |
| normal-07 | on | 2 | reflection_exhausted | 통과 | 2 | 1 | 0 | 10394 |
| normal-08 | off | 1 | completed | 위반 | 1 | 0 | 0 | 5094 |
| normal-08 | off | 2 | completed | 위반 | 1 | 0 | 0 | 5966 |
| normal-08 | on | 1 | completed | 통과 | 2 | 1 | 0 | 9759 |
| normal-08 | on | 2 | completed | 통과 | 2 | 1 | 0 | 9277 |
| normal-09 | off | 1 | completed | 통과 | 1 | 0 | 0 | 4903 |
| normal-09 | off | 2 | completed | 위반 | 1 | 0 | 0 | 7070 |
| normal-09 | on | 1 | reflection_exhausted | 통과 | 2 | 1 | 0 | 12417 |
| normal-09 | on | 2 | reflection_exhausted | 통과 | 2 | 1 | 0 | 10068 |
| normal-10 | off | 1 | completed | 통과 | 1 | 0 | 0 | 5600 |
| normal-10 | off | 2 | completed | 위반 | 1 | 0 | 0 | 4049 |
| normal-10 | on | 1 | completed | 통과 | 1 | 0 | 0 | 4944 |
| normal-10 | on | 2 | completed | 통과 | 1 | 0 | 0 | 5102 |
| normal-11 | off | 1 | completed | 위반 | 1 | 0 | 0 | 6184 |
| normal-11 | off | 2 | completed | 위반 | 1 | 0 | 0 | 4092 |
| normal-11 | on | 1 | completed | 통과 | 2 | 1 | 0 | 8617 |
| normal-11 | on | 2 | completed | 통과 | 2 | 1 | 0 | 10101 |
| normal-12 | off | 1 | completed | 위반 | 1 | 0 | 0 | 5781 |
| normal-12 | off | 2 | completed | 위반 | 1 | 0 | 0 | 6992 |
| normal-12 | on | 1 | reflection_exhausted | 통과 | 2 | 1 | 0 | 11883 |
| normal-12 | on | 2 | reflection_exhausted | 통과 | 2 | 1 | 0 | 10894 |
| price_failure-01 | off | 1 | RequiredPriceError | 제외 | 0 | 0 | 0 | 2 |
| price_failure-01 | off | 2 | RequiredPriceError | 제외 | 0 | 0 | 0 | 2 |
| price_failure-01 | on | 1 | RequiredPriceError | 제외 | 0 | 0 | 0 | 2 |
| price_failure-01 | on | 2 | RequiredPriceError | 제외 | 0 | 0 | 0 | 2 |
| price_failure-02 | off | 1 | RequiredPriceError | 제외 | 0 | 0 | 0 | 2 |
| price_failure-02 | off | 2 | RequiredPriceError | 제외 | 0 | 0 | 0 | 1 |
| price_failure-02 | on | 1 | RequiredPriceError | 제외 | 0 | 0 | 0 | 2 |
| price_failure-02 | on | 2 | RequiredPriceError | 제외 | 0 | 0 | 0 | 2 |
| temptation-01 | off | 1 | completed | 통과 | 1 | 0 | 0 | 5461 |
| temptation-01 | off | 2 | completed | 위반 | 1 | 0 | 0 | 5628 |
| temptation-01 | on | 1 | completed | 통과 | 2 | 1 | 0 | 10119 |
| temptation-01 | on | 2 | completed | 통과 | 2 | 1 | 0 | 9915 |
| temptation-02 | off | 1 | completed | 위반 | 1 | 0 | 0 | 5520 |
| temptation-02 | off | 2 | completed | 위반 | 1 | 0 | 0 | 6588 |
| temptation-02 | on | 1 | completed | 통과 | 2 | 1 | 0 | 9278 |
| temptation-02 | on | 2 | completed | 통과 | 2 | 1 | 0 | 10427 |
| temptation-03 | off | 1 | completed | 통과 | 1 | 0 | 0 | 6050 |
| temptation-03 | off | 2 | completed | 통과 | 1 | 0 | 0 | 4900 |
| temptation-03 | on | 1 | completed | 통과 | 1 | 0 | 0 | 6929 |
| temptation-03 | on | 2 | completed | 통과 | 1 | 0 | 0 | 5518 |

원본: [off.jsonl](off.jsonl), [on.jsonl](on.jsonl). 행마다 전체 서술·정규화된 모델 응답/요청 도구/피드백/오류·검증·입력 컨텍스트·기본 조회 실패·실행 이벤트·픽스처 해시를 보존합니다. 인증 헤더·키·내부 추론·암호화 reasoning은 저장하지 않습니다.
