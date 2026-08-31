# 현재 프로젝트 구조 비교 및 추가 폴더 제안

> 이 문서는 팀 회의를 위한 구조 비교 초안입니다. 선생님이 특정 폴더명을 강제한 것은 아니므로, `필수 시스템 영역`, `역할상 필요한 구조`, `선택적으로 추가할 구조`를 구분해서 판단합니다. 이 문서는 폴더 생성 지시서가 아니라 책임 분담을 논의하기 위한 자료입니다.

## 1. 확인 목적

현재 프로젝트에는 Frontend, Backend, MCP Server, Database의 기본 골격이 있다. 선생님이 설명한 전체 개발 구조 및 수업 요소와 비교하여 다음을 확인한다.

- 현재 구조에 이미 반영된 영역
- 명확하게 빠진 시스템 영역
- 폴더는 있지만 내부 구현이 비어 있는 영역
- 개발이 진행되면 역할별 분리가 필요한 영역
- 폴더를 추가하기 전에 팀에서 결정해야 할 사항

## 2. 현재 프로젝트 구조

```text
aio-p2-5th-team-stock/
├─ backend/
│  ├─ app/
│  │  ├─ clients/
│  │  ├─ core/
│  │  ├─ routers/
│  │  ├─ schemas/
│  │  └─ services/
│  └─ scripts/
├─ frontend/
│  └─ app.py
├─ mcp_server/
│  └─ stock_mcp/
│     ├─ stock_server.py
│     └─ app/
│        ├─ clients/
│        ├─ core/
│        ├─ schemas/
│        ├─ services/
│        └─ tools/
├─ db/
│  ├─ schema.sql
│  └─ seed.sql
└─ gide/
```

현재 구조는 각 컴포넌트가 별도의 `.env.example`과 `requirements.txt`를 가지므로, 팀원별 컴퓨터에서 독립적으로 실행할 수 있는 방향을 반영하고 있다.

## 3. 선생님이 제시한 시스템 영역과 비교

선생님 자료에서 확인되는 전체 시스템 및 수업 요소는 다음과 같다.

```text
Frontend
Backend
MCP Server
Database Server
Redis Server
AI Agent
RAG
Login / Admin / User
SSE
LLM
Multimodal(MOV, MP3)
System Architecture
```

현재 반영 상태는 다음과 같다.

| 영역 | 현재 상태 | 판단 |
|---|---|---|
| Frontend | `frontend/app.py` 존재 | 기본 실행 골격 있음 |
| Backend | FastAPI와 역할별 기본 폴더 존재 | 기본 실행 골격 있음 |
| MCP Server | FastMCP와 `clients/services/tools` 구조 존재 | 기본 실행 골격 있음 |
| Database | 스키마와 시드 존재 | 설계 골격 있음 |
| Redis Server | 설정·실행 구조 없음 | 명확하게 빠진 시스템 영역 |
| AI Agent | Agent 위치와 실행 구조 없음 | 역할 및 위치 결정 필요 |
| RAG | DB 스키마는 있으나 수집·청킹·임베딩·검색 구현 없음 | 구조 일부만 반영 |
| Login/Admin/User | 사용자 테이블만 있고 인증·권한 구조 없음 | 구현 위치 결정 필요 |
| SSE | 관련 구조 없음 | Backend·Frontend 양쪽에 필요 |
| LLM | API 키 설정만 존재 | Client·Provider 구조 필요 |
| Multimodal | MOV·MP3 처리 위치 없음 | 담당 컴포넌트 결정 필요 |
| System Architecture | README 구조도 존재 | Redis와 세부 연결 보완 필요 |

## 4. 명확하게 빠진 시스템 영역

### 4.1 Redis

선생님이 제시한 전체 구성에는 Redis Server가 포함되어 있지만 현재 프로젝트에는 Redis 실행 또는 설정 영역이 없다.

Redis는 별도의 Python 애플리케이션이 아니므로 반드시 `redis_server`라는 코드 폴더를 만들 필요는 없다. 팀 실행 방식에 따라 다음 중 하나를 선택할 수 있다.

#### 선택안 A: Redis 설정 폴더

```text
redis/
└─ redis.conf
```

#### 선택안 B: 인프라 폴더

```text
infra/
├─ postgres/
└─ redis/
```

#### 선택안 C: 루트 실행 설정

```text
docker-compose.yml
```

PostgreSQL과 Redis를 하나의 실행 설정에서 함께 띄우는 방식이다.

#### Redis의 프로젝트 역할

- 현재가·뉴스 단기 캐시
- 동일 종목·동일 질문 분석 결과 캐시
- 분석 작업 진행 상태
- SSE 이벤트 또는 작업 상태 공유
- 필요할 경우 로그인 세션

Redis 데이터가 삭제되더라도 사용자 계정, 투자 메모, 원문 문서, 최종 분석 결과는 PostgreSQL에 남아 있어야 한다.

## 5. Backend에서 추가를 검토할 구조

현재 Backend의 `routers`, `schemas`, `services`, `clients`, `core`는 좋은 기본 골격이다. 다음 구조는 실제 기능의 책임을 명확히 하기 위해 추가를 검토한다.

### 5.1 AI Agent

```text
backend/app/agents/
├─ stock_agent.py
├─ prompts.py
└─ response_builder.py
```

담당 역할:

- 사용자 질문 분류
- 질문에 필요한 MCP Tool 선택
- Tool 결과 취합
- 사실·해석·주의점·출처가 구분된 답변 생성
- 필요한 정보가 없을 때 추측하지 않는 응답 처리

AI Agent는 수업의 핵심 요소이므로 Backend 내부에 둘지 별도 서비스로 분리할지 반드시 결정해야 한다. MVP에서는 Backend 내부가 단순하다.

### 5.2 Repository

```text
backend/app/repositories/
├─ user_repository.py
├─ note_repository.py
└─ analysis_repository.py
```

담당 역할:

- 사용자·투자 메모·분석 기록의 DB 접근
- SQL과 업무 로직 분리
- Backend가 직접 소유할 데이터 범위 관리

Repository는 필수 폴더명은 아니지만, Service 안에 SQL이 섞이는 것을 줄이는 데 도움이 된다.

### 5.3 LLM Provider 또는 Client

```text
backend/app/providers/
├─ base.py
├─ openai_provider.py
└─ ollama_provider.py
```

또는 현재 `clients` 아래에 다음처럼 둘 수 있다.

```text
backend/app/clients/
└─ llm_client.py
```

담당 역할:

- OpenAI·Ollama 등 LLM 호출 방식 통일
- 모델 교체 시 Agent와 Service 코드 변경 최소화
- 타임아웃·재시도·응답 형식 검증

MVP에서 LLM 하나만 확정한다면 `clients/llm_client.py`로 시작하고, 실제 교체 요구가 생길 때 Provider 구조로 확장할 수 있다.

### 5.4 Backend 내부 공통 파일

현재 존재하는 `core` 안에 다음 역할의 파일을 추가할 수 있다.

```text
backend/app/core/
├─ config.py
├─ database.py
├─ redis.py
├─ security.py
└─ logging.py
```

- `database.py`: Backend가 소유하는 사용자·메모·분석 기록 DB 연결
- `redis.py`: 캐시와 분석 진행 상태 연결
- `security.py`: 비밀번호 해시, 인증 토큰, Admin/User 권한
- `logging.py`: 요청·Agent·MCP 오류 기록

## 6. RAG 폴더의 위치 결정

선생님 예시에서는 청킹, 임베딩, 벡터 저장소, PDF 수집 등을 역할별로 분리했다. 현재 프로젝트에서는 RAG 스키마만 있고 실제 처리 위치가 정해지지 않았다.

### 선택안 A: Backend가 RAG 수집을 담당

```text
backend/app/rag/
├─ chunking.py
├─ embedding.py
├─ ingestion.py
└─ retrieval.py
```

장점:

- 관리자 업로드 API와 가까움
- 문서 등록 흐름을 Backend가 직접 관리하기 쉬움

주의점:

- MCP에도 RAG 조회 기능을 만들면 책임이 중복될 수 있음

### 선택안 B: MCP Server가 RAG를 담당

```text
mcp_server/stock_mcp/app/
├─ clients/
│  ├─ embedding_client.py
│  └─ vector_store.py
├─ services/
│  ├─ ingestion_service.py
│  └─ retrieval_service.py
└─ tools/
   └─ rag_tools.py
```

장점:

- Agent가 RAG를 하나의 MCP Tool로 사용할 수 있음
- 뉴스·공시·커뮤니티 조회 책임과 가까움
- 수업에서 설명한 `MCP를 통한 RAG Tool`을 보여주기 좋음

### 회의 제안

MVP에서는 다음처럼 역할을 나누는 방안을 우선 검토한다.

- Backend: 관리자 업로드 요청, 사용자 권한, 작업 시작
- MCP: 문서 처리, 청킹, 임베딩, pgvector 저장과 검색

이 경우 Backend는 MCP의 수집 Tool을 호출하고, 실제 RAG 로직은 MCP에 한 번만 구현한다.

## 7. Frontend에서 추가를 검토할 구조

현재 Frontend는 `app.py` 하나뿐이므로 기능이 늘어나면 화면, API 요청, 상태가 한 파일에 섞일 수 있다.

```text
frontend/
├─ app.py
├─ pages/
│  ├─ login.py
│  ├─ stock_dashboard.py
│  ├─ my_notes.py
│  └─ admin_documents.py
├─ components/
│  ├─ stock_search.py
│  ├─ sentiment_card.py
│  ├─ evidence_card.py
│  ├─ source_list.py
│  └─ analysis_chat.py
├─ services/
│  ├─ api_client.py
│  └─ sse_client.py
└─ state/
   └─ session.py
```

### 폴더별 역할

| 폴더 | 역할 |
|---|---|
| `pages` | 로그인, 종목 분석, 메모, 관리자 등 화면 단위 구성 |
| `components` | 여러 화면에서 재사용할 UI 요소 |
| `services` | Backend HTTP·SSE 통신 |
| `state` | 로그인 사용자, 선택 종목, 분석 작업 상태 |

Frontend는 Backend만 호출하며 DB, Redis, MCP, 외부 주식 API에 직접 접근하지 않는다.

## 8. MCP Server의 현재 상태

MCP Server에는 선생님이 설명한 기본 역할 폴더가 이미 존재한다.

```text
mcp_server/stock_mcp/app/
├─ clients/
├─ core/
├─ schemas/
├─ services/
└─ tools/
```

따라서 새로운 상위 폴더가 부족한 것보다 각 역할의 구현 파일이 아직 없는 상태에 가깝다.

### 향후 들어갈 수 있는 파일 예시

```text
clients/
├─ market_client.py
├─ news_client.py
├─ dart_client.py
├─ community_client.py
├─ embedding_client.py
└─ vector_store.py

services/
├─ market_service.py
├─ news_service.py
├─ disclosure_service.py
├─ community_service.py
└─ retrieval_service.py

tools/
├─ stock_tools.py
├─ market_tools.py
├─ news_tools.py
├─ disclosure_tools.py
├─ community_tools.py
└─ rag_tools.py
```

### 현재 MCP 구조에서 중요한 점

- `tools`에는 MCP 입출력과 설명만 둔다.
- 외부 API 호출은 `clients`가 담당한다.
- 정제·계산·검색 규칙은 `services`가 담당한다.
- Tool마다 기준 시각, 출처, 조회 상태를 반환한다.
- MCP 서버를 처음부터 여러 개로 나누지 않고 한 개로 시작할 수 있다.

## 9. Database 구조에서 추가를 검토할 영역

현재 `db`에는 `schema.sql`과 `seed.sql`이 있어 설계의 시작점은 마련되어 있다.

### 9.1 마이그레이션

```text
db/
├─ migrations/
├─ schema.sql
└─ seed.sql
```

여러 팀원이 테이블 구조를 변경할 경우 같은 순서로 DB를 갱신하기 위한 영역이다. 초기에는 필수가 아니지만 구조 변경이 시작되면 필요성이 커진다.

### 9.2 Database Server 실행 설정

README에는 PostgreSQL과 pgvector를 사용한다고 설명되어 있지만, 현재 저장소에는 Database Server를 동일한 방식으로 실행하기 위한 설정이 없다.

검토할 수 있는 방식:

```text
infra/postgres/
```

또는 루트의 `docker-compose.yml`에서 PostgreSQL과 Redis를 함께 정의한다.

### 9.3 DB에 추가로 필요한 역할

- 사용자 인증과 Admin/User 권한
- 종목 마스터
- 가격·거래량 저장 여부
- 투자자별 수급
- 원문 문서와 RAG 청크 관계
- 사용자 메모 원본
- 시장 심리·근거 강도 스냅샷
- 분석 실행과 사용 근거 기록

구체적인 테이블 제안은 `04_DATABASE_GUIDE.md`를 참고한다.

## 10. 멀티모달 처리 위치

수업 요구사항의 MOV·MP3 처리 위치가 현재 구조에는 없다.

주식 서비스에서는 IR 영상, 실적발표 음성, 사용자 투자 음성 메모를 텍스트로 변환하여 RAG에 넣는 방향으로 연결할 수 있다.

### MCP가 처리하는 예시

```text
mcp_server/stock_mcp/app/
├─ clients/
│  └─ transcription_client.py
├─ services/
│  └─ multimodal_service.py
└─ tools/
   └─ multimodal_tools.py
```

### Backend가 처리하는 예시

```text
backend/app/services/
└─ document_ingestion_service.py
```

### 회의 제안

- Frontend: 파일 업로드 화면
- Backend: 권한·파일 검증·작업 시작
- MCP: 음성 추출·텍스트 변환·RAG 저장

이렇게 나누면 RAG 수집과 멀티모달 처리를 같은 흐름으로 관리할 수 있다.

## 11. 추천 목표 구조 예시

아래 구조는 회의를 위한 예시이며 모두 즉시 만들 필요는 없다.

```text
aio-p2-5th-team-stock/
├─ backend/
│  └─ app/
│     ├─ agents/             # 추가 검토
│     ├─ clients/            # 존재
│     ├─ core/               # 존재
│     ├─ repositories/       # 추가 검토
│     ├─ routers/            # 존재
│     ├─ schemas/            # 존재
│     └─ services/           # 존재
├─ frontend/
│  ├─ pages/                 # 추가 검토
│  ├─ components/            # 추가 검토
│  ├─ services/              # 추가 검토
│  └─ state/                 # 추가 검토
├─ mcp_server/
│  └─ stock_mcp/app/
│     ├─ clients/            # 존재, 구현 파일 필요
│     ├─ core/               # 존재, 구현 파일 필요
│     ├─ schemas/            # 존재, 구현 파일 필요
│     ├─ services/           # 존재, 구현 파일 필요
│     └─ tools/              # 존재, 구현 파일 필요
├─ db/
│  ├─ migrations/            # 선택적으로 추가
│  ├─ schema.sql
│  └─ seed.sql
├─ infra/                    # Redis·PostgreSQL 실행 방식에 따라 추가
│  ├─ postgres/
│  └─ redis/
└─ gide/
```

## 12. 지금 바로 만들 필요가 없는 폴더

폴더 구조가 자세할수록 좋은 것은 아니다. 다음 구조는 실제 필요가 생겼을 때 추가한다.

- 여러 종류의 LLM을 사용하지 않는다면 복잡한 `providers` 계층
- 데이터가 적은 상태의 별도 벡터 DB 서버
- 하나의 MCP로 충분한 상태의 여러 MCP 서버 폴더
- 커뮤니티 기능이 확정되지 않은 상태의 게시글·댓글 모듈
- 실제 멀티모달 시나리오가 없는 상태의 대규모 처리 파이프라인
- 최적화 필요성이 확인되지 않은 큐·워커 분리

빈 폴더를 먼저 만드는 것보다 컴포넌트 간 입출력 계약과 책임을 먼저 확정한다.

## 13. 우선 결정해야 할 사항

1. Redis와 PostgreSQL을 Docker로 실행할 것인가?
2. AI Agent를 Backend 내부에 둘 것인가?
3. RAG 청킹·임베딩·검색은 Backend와 MCP 중 누가 담당할 것인가?
4. 멀티모달 변환은 어느 컴포넌트가 담당할 것인가?
5. Backend가 직접 접근할 DB 테이블은 무엇인가?
6. MCP가 접근할 DB 테이블은 무엇인가?
7. LLM을 하나로 확정할지 Provider 교체 구조를 만들지
8. Frontend의 페이지 분리 시점을 언제로 할지
9. DB 마이그레이션 도구를 도입할지
10. 각 컴포넌트를 팀원별 컴퓨터에서 어떻게 실행할지

## 14. 구조 확정 우선순위

### 1순위: 컴포넌트 책임

- Frontend → Backend만 호출
- Backend → 인증·Agent·SSE·응답 조립
- MCP → 투자 정보·외부 API·RAG Tool
- PostgreSQL → 영구 데이터
- Redis → 캐시·진행 상태

### 2순위: 최소 통신

```text
Frontend → Backend → MCP → DB → Backend → Frontend
```

Redis까지 연결하여 캐시와 작업 상태를 확인한다.

### 3순위: 역할별 파일 분리

최소 통신이 성공한 다음 실제 기능이 들어갈 때 `agents`, `pages`, `repositories` 등의 폴더를 추가한다.

## 15. 최종 정리

현재 확실하게 빠진 시스템 영역은 다음과 같다.

```text
Redis Server
AI Agent 실행 영역
멀티모달 처리 영역
실제 RAG 수집·검색 구현
Frontend·Backend·MCP 간 실제 통신 구현
```

추가를 검토할 대표 폴더는 다음과 같다.

```text
backend/app/agents/
backend/app/repositories/
frontend/pages/
frontend/components/
frontend/services/
frontend/state/
db/migrations/
infra/postgres/
infra/redis/
```

반면 Backend와 MCP의 `routers`, `services`, `clients`, `schemas`, `core`, `tools` 기본 구분은 이미 존재한다. 따라서 현재 구조를 다시 만드는 것이 아니라, 책임을 확정하고 빠진 시스템 영역을 단계적으로 채우는 방향이 적절하다.

