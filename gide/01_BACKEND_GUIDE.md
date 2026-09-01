# Backend 개발 방향 제안서

> 이 문서는 팀 회의를 위한 Backend 설계 예시입니다. 실제 API 경로, 인증 방식, 폴더명은 팀 합의 후 확정합니다.

## 1. Backend의 역할

Backend는 Frontend와 모든 내부 시스템 사이의 중심 창구다.

Backend가 직접 뉴스 크롤링, DART 파싱, 벡터 검색을 모두 구현하는 것이 아니라 다음 업무에 집중한다.

- 회원가입·로그인·권한 확인
- Frontend 요청 검증
- AI Agent 실행
- MCP Server 호출 및 결과 취합
- Redis 캐시 확인
- SSE 진행 이벤트 전달
- 질문·답변·분석 결과 저장
- 사용자에게 반환할 응답 형식 통일

## 2. 권장 요청 흐름

```text
Frontend 요청
  → Router에서 입력 검증
  → 인증·권한 확인
  → Service에서 업무 흐름 실행
  → Redis 캐시 확인
  → Agent가 MCP Tool 선택
  → MCP Client가 MCP Server 호출
  → LLM이 근거를 설명
  → Repository가 결과 저장
  → Schema 형식으로 Frontend에 반환
```

Router에 분석 코드를 몰아넣지 않고, Router는 요청 수신과 응답 반환만 담당하도록 한다.

## 3. 폴더 구조 예시

현재 구조를 유지하면서 아래 역할을 추가하는 방향을 논의할 수 있다.

```text
backend/
├─ .env.example
├─ requirements.txt
└─ app/
   ├─ main.py                 # FastAPI 앱 생성, Router 등록
   ├─ core/
   │  ├─ config.py            # 환경변수
   │  ├─ security.py          # 비밀번호 해시, 토큰, 권한
   │  ├─ database.py          # Backend 전용 DB 연결
   │  ├─ redis.py             # Redis 연결
   │  └─ logging.py           # 공통 로그
   ├─ routers/
   │  ├─ auth.py              # 회원가입·로그인
   │  ├─ stocks.py            # 검색·종목 요약
   │  ├─ analysis.py          # AI 분석 요청·SSE
   │  ├─ notes.py             # 사용자 투자 메모 CRUD
   │  └─ admin.py             # 관리자 자료 관리
   ├─ schemas/
   │  ├─ auth.py
   │  ├─ stock.py
   │  ├─ analysis.py
   │  ├─ note.py
   │  └─ common.py
   ├─ services/
   │  ├─ auth_service.py
   │  ├─ stock_service.py
   │  ├─ analysis_service.py
   │  ├─ note_service.py
   │  └─ admin_service.py
   ├─ agents/
   │  ├─ stock_agent.py       # 질문 판단 및 Tool 실행 계획
   │  ├─ prompts.py           # 시스템 프롬프트
   │  └─ response_builder.py  # 사실·해석·출처 응답 조립
   ├─ clients/
   │  ├─ mcp_client.py
   │  ├─ llm_client.py
   │  └─ redis_client.py
   └─ repositories/
      ├─ user_repository.py
      ├─ note_repository.py
      └─ analysis_repository.py
```

폴더를 처음부터 전부 만들 필요는 없다. 기능이 실제로 추가될 때 해당 역할의 파일을 만드는 방식이 좋다.

## 4. API 예시

아래 경로는 팀 회의를 위한 예시다.

### 인증

| Method | Path | 역할 |
|---|---|---|
| POST | `/auth/signup` | 회원가입 |
| POST | `/auth/login` | 로그인 |
| POST | `/auth/logout` | 로그아웃 |
| GET | `/users/me` | 현재 사용자 정보 |

### 종목

| Method | Path | 역할 |
|---|---|---|
| GET | `/stocks/search?query=삼성전자` | 기업명·종목코드 검색 |
| GET | `/stocks/{stock_code}/summary` | 가격·수급·시장 심리 요약 |
| GET | `/stocks/{stock_code}/evidence` | 뉴스·공시·커뮤니티 근거 목록 |

### AI 분석

| Method | Path | 역할 |
|---|---|---|
| POST | `/analyses` | 분석 작업 생성 |
| GET | `/analyses/{analysis_id}` | 분석 결과 조회 |
| GET | `/analyses/{analysis_id}/stream` | SSE 진행 상황 및 답변 수신 |

### 사용자 메모

| Method | Path | 역할 |
|---|---|---|
| POST | `/stocks/{stock_code}/notes` | 투자 메모 작성 |
| GET | `/stocks/{stock_code}/notes` | 종목별 메모 목록 |
| PATCH | `/notes/{note_id}` | 메모 수정 |
| DELETE | `/notes/{note_id}` | 메모 삭제 |

### 관리자

| Method | Path | 역할 |
|---|---|---|
| POST | `/admin/documents` | PDF·MP3·MOV 자료 등록 |
| GET | `/admin/documents` | 등록 자료 조회 |
| DELETE | `/admin/documents/{document_id}` | 자료와 청크 삭제 |
| POST | `/admin/ingestions/{document_id}` | 청킹·임베딩 작업 시작 |

## 5. 종목 요약 응답 구조 예시

Frontend가 여러 API 결과를 직접 조합하지 않도록 Backend가 화면에 필요한 형식으로 정리하는 방식을 제안한다.

```json
{
  "stock": {
    "code": "005930",
    "name": "삼성전자"
  },
  "observed_at": "데이터 기준 시각",
  "market": {
    "price": 0,
    "change_rate": 0.0,
    "volume_ratio": 0.0
  },
  "flow": {
    "individual": 0,
    "foreign": 0,
    "institution": 0
  },
  "sentiment": {
    "temperature": 0,
    "label": "fear | neutral | greed",
    "reasons": []
  },
  "evidence": {
    "strength": 0,
    "label": "low | medium | high",
    "reasons": []
  },
  "top_topics": [],
  "sources": []
}
```

위 값과 명칭은 예시이며 팀에서 계산 방식과 화면 요구사항을 정한 뒤 확정한다.

## 6. AI Agent 설계 방향

Agent는 질문 유형에 따라 필요한 MCP Tool만 호출한다.

| 질문 유형 | 호출 후보 |
|---|---|
| 현재 가격 | 종목 검색, 시세 Tool |
| 최근 상승·하락 맥락 | 시세, 거래량, 수급, 뉴스, 공시 Tool |
| 사람들의 반응 | 커뮤니티 분석 Tool |
| 기업 위험 요소 | 공시 RAG, 뉴스 RAG |
| 개인 관점 비교 | 사용자 메모 RAG, 뉴스, 공시 |

### Agent 처리 단계

1. 질문에서 종목과 기간을 확인한다.
2. 가격 질문, 근거 질문, 커뮤니티 질문, 개인 메모 질문 등을 분류한다.
3. 필요한 MCP Tool을 선택한다.
4. Tool 결과에서 출처·기준 시각·데이터 누락을 확인한다.
5. LLM에 질문과 근거를 전달한다.
6. 사실, 해석, 주의점, 출처를 분리한 응답을 만든다.

Agent가 답변에 필요한 자료를 확보하지 못한 경우 추측하지 않고 `현재 확보한 자료만으로 원인을 단정하기 어렵다`고 응답해야 한다.

## 7. SSE 설계 방향

분석 과정이 길어질 때 Frontend가 멈춘 것처럼 보이지 않도록 진행 상태를 전송한다.

### 이벤트 예시

```text
analysis_started
stock_resolved
market_data_loaded
flow_data_loaded
news_loaded
disclosures_loaded
community_analyzed
answer_generating
analysis_completed
analysis_failed
```

각 이벤트에는 `analysis_id`, 진행 메시지, 진행률, 발생 시각을 포함하는 방향을 논의한다.

SSE 연결이 끊어져도 사용자가 `analysis_id`로 최종 결과를 다시 조회할 수 있어야 한다.

## 8. Redis 사용 방향

Redis는 다음 세 가지 목적으로 제한하여 시작하는 것이 좋다.

1. 짧은 주기의 시세·뉴스 결과 캐시
2. 동일 종목·동일 기간·동일 질문 결과 캐시
3. 분석 진행 상태와 SSE 이벤트 저장

캐시 키에는 종목코드, 데이터 종류, 기간, 데이터 버전이 포함되어야 한다. 새로운 공시나 뉴스가 저장되면 관련 캐시를 무효화할 수 있어야 한다.

## 9. DB 접근 책임

Backend가 직접 관리할 데이터:

- 사용자 계정
- 비밀번호 해시와 권한
- 관심 종목
- 사용자 투자 메모 CRUD
- 질문·답변·분석 실행 기록

MCP를 통해 조회할 데이터:

- 종목 정보
- 가격·수급
- 뉴스·공시
- 커뮤니티 분석
- RAG 근거

같은 PostgreSQL을 사용하더라도 Backend와 MCP의 DB 계정과 접근 범위를 분리하는 방안을 검토한다.

## 10. 오류 처리 원칙

- 외부 데이터가 없으면 빈 값을 정상 응답으로 구분한다.
- 외부 API 장애와 `조회 결과 없음`을 구분한다.
- 일부 Tool이 실패해도 확보한 근거로 제한된 답변을 제공할 수 있다.
- 모든 응답에 데이터 기준 시각을 포함한다.
- LLM 응답은 정해진 Schema로 검증한다.
- 투자 추천으로 오해할 표현을 제한한다.

## 11. Backend 개발 순서 제안

1. 설정과 공통 응답 Schema 정리
2. Frontend에서 호출할 샘플 종목 요약 API
3. MCP Client 연결과 `ping` 확인
4. MCP 샘플 Tool 결과를 Frontend까지 전달
5. Redis 연결과 캐시
6. 분석 작업과 SSE
7. Agent와 LLM 응답 구조
8. 로그인·권한
9. 투자 메모 CRUD
10. 관리자 자료 등록
11. 오류·로그·테스트 정리

## 12. Backend 회의 질문

- 인증을 어떤 방식으로 유지할 것인가? <없음 jwt제외>
- Backend와 MCP가 각각 어떤 DB 테이블을 소유할 것인가?  <동일>
- Agent를 Backend 내부에 둘 것인가, 별도 서비스로 분리할 것인가? <내부>
- SSE 분석 작업을 서버 메모리와 Redis 중 어디에서 관리할 것인가? <redis>
- LLM 제공자를 교체할 수 있는 공통 Client가 필요한가? <>
- 일부 데이터 조회가 실패했을 때 어떤 응답을 제공할 것인가?
- API 응답 형식을 Frontend와 언제 확정할 것인가?

