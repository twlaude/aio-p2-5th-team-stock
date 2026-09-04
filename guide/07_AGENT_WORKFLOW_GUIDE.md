# 주식 분석 Agent Workflow 적용 가이드

> 참고한 수업 자료
> `C:\Port_수업자료\mini\mini_agent\mini_agent_06_agent_workflow`
> `C:\Port_수업자료\aidevs\05_llm-agent-orchestration\06_agent-workflow`

## 1. 프로젝트에서 Agent가 있는 위치

Agent는 Backend나 각 MCP 서버가 아니라 `mcp_client` 통합 서버에 둔다.

```text
MCP Client
├─ Workflow
├─ Stock Analysis Agent
├─ Agent Runtime
├─ LLM Provider
└─ MCP Clients
   ├─ Price MCP
   ├─ News MCP
   ├─ Disclosure MCP
   └─ Community MCP
```

주가·뉴스·공시·커뮤니티 MCP 서버는 Agent가 아니다. 각 서버는 조회와 검색을 제공하는 Tool 서버다.

## 2. Workflow와 Agent의 책임

### Workflow

개발자가 반드시 통제해야 하는 순서를 담당한다.

```text
입력 검증
→ 회사 확인
→ 필수 데이터 수집
→ Agent 실행
→ 출처 검증
→ 응답 Schema 검증
→ Backend 반환
```

### Stock Analysis Agent

정해진 Goal과 현재 State를 보고 다음 행동을 판단한다.

- 추가 뉴스가 필요한가
- 공시 상세정보를 다시 확인해야 하는가
- 커뮤니티 표본이 부족한가
- 여러 근거가 충돌하는가
- 자료가 충분하여 답변을 종료할 수 있는가

## 3. 초기에는 Single Agent

MCP 서버가 네 개라고 해서 Multi-Agent가 아니다. 판단 주체, Goal과 State가 하나이므로 현재 구조는 여러 Tool을 사용하는 Single Agent다.

```text
Stock Analysis Agent
├─ Price Tools
├─ News Tools
├─ Disclosure Tools
└─ Community Tools
```

뉴스 Agent, 공시 Agent, 커뮤니티 Agent로 바로 나누지 않는다. 독립 Goal, 전문 Prompt, 권한, 완료 조건과 평가 기준이 실제로 달라져 Single Agent의 품질이 떨어질 때 Multi-Agent를 검토한다.

## 4. Agent 구성요소

### Goal

> 검색한 종목에 대해 주가, 뉴스, 공식 공시, 커뮤니티 반응을 근거와 함께 비교하고, 추천 없이 사용자가 확인할 공통 시장 맥락을 완성한다.

### State

```text
run_id
goal
question
company_name
stock_code
status
current_step
tool_results
llm_calls
tool_calls
answer
termination_reason
trace
```

대화 History, Agent 업무 State, 장기 Memory, Trace는 같은 개념으로 취급하지 않는다.

### Allowed Tools

초기 확정 Tool:

```text
get_stock_quote
search_news
get_recent_disclosures
get_disclosure_detail
search_annual_report
get_community_reaction
```

Model에는 현재 Agent에 허용된 Tool Schema만 제공한다.

### Loop

```text
Goal과 State를 Model에 전달
→ Tool Call 또는 최종 답변 선택
→ Runtime이 Tool 이름과 arguments 검증
→ MCP Tool 실행
→ Tool Result를 State와 Trace에 기록
→ Tool Result를 Model에 다시 전달
→ 추가 Tool 또는 종료 재판단
```

Model이 요청한 Tool Call은 실행 명령이 아니라 제안이다. 실제 실행 권한은 Runtime과 Workflow가 가진다.

## 5. 종료 조건

```text
completed             필요한 근거와 답변이 완성됨
no_data               필수 자료가 없음
partial_completed     일부 MCP 실패, 가능한 근거로 제한된 결과 완성
model_error           Model 호출 실패
invalid_tool_call     허용되지 않은 Tool 또는 잘못된 arguments
mcp_tool_error         MCP Tool 실행 실패
max_steps_exceeded    최대 반복 후 추가 Tool 요청이 남음
workflow_timeout      전체 허용 시간 초과
```

모든 실행은 `termination_reason`을 남긴다. 권한 오류와 잘못된 Tool Call을 무의미하게 반복하지 않는다.

## 6. 필수 데이터와 추가 조회

우리 서비스의 FE2에는 주가·뉴스·공시·커뮤니티 네 영역이 기본적으로 필요하다. 따라서 첫 조회는 Workflow가 병렬로 실행하는 방향이 적합하다.

```text
Workflow 기본 조회
├─ 현재 주가
├─ 최근 뉴스
├─ 최근 공시
└─ 커뮤니티 반응
```

Agent는 기본 결과를 관찰한 뒤 상세 Tool을 추가로 호출할지 판단한다. 이렇게 하면 필수 화면 데이터는 예측 가능하게 확보하면서 Agent의 Result 기반 재판단도 보여줄 수 있다.

## 7. 부분 실패

```text
News 성공
Disclosure 성공
Community 실패
```

커뮤니티가 선택 정보라면 뉴스와 공시로 `partial_completed` 결과를 만들고 제한사항을 표시한다. 필수 공식 근거가 전부 실패하면 성공한 것처럼 답변하지 않는다.

## 8. Trace

Trace에는 다음 내용을 구조적으로 기록한다.

- 실행 ID
- Workflow 단계
- Model 호출 횟수
- 선택한 Tool
- 검증된 arguments
- MCP 서버와 endpoint 종류
- Tool Result의 상태
- 반복 단계
- 종료 이유
- 전체 지연 시간

비밀키, 인증 토큰, 불필요한 개인정보, 전체 내부 Prompt는 Trace에 저장하지 않는다.

## 9. 테스트 시나리오

1. Tool 없이 바로 답변 가능한 요청
2. 뉴스 Tool 한 번 후 종료
3. 공시 결과 후 상세 공시 추가 조회
4. 빈 검색 결과
5. 허용되지 않은 Tool 요청
6. 잘못된 JSON arguments
7. 한 MCP 서버 오류
8. Model 오류
9. 마지막 Tool Result 후 정상 종료
10. 최대 단계까지 계속 Tool을 요청하는 경우

## 10. LangGraph 적용 여부

초기에는 수업 예제처럼 순수 Python Runtime으로 Goal, State, Tool Result, Loop와 종료를 먼저 이해하고 구현하는 방향이 적합하다.

LangGraph는 다음 요구가 실제로 생겼을 때 선택적으로 검토한다.

- 복잡한 조건 분기
- Checkpoint
- 중단 후 재개
- Human Approval
- 장시간 실행 추적

LangGraph를 사용했다고 Agent가 되는 것이 아니며, 사용하지 않아도 Agent Workflow를 구현할 수 있다.
