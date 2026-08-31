# 📈 stock_insight — AIO P2 5팀

> **종목명 하나를 입력하면, 그 종목에 대한 근거 있는 투자 판단 재료를 쉽게 풀어주는 서비스**

재무제표 · 주요 수치 · 뉴스 · **커스텀 토스 커뮤니티 공포탐욕지수**(개미 분위기 요약)를
한 번에 분석해서, 어려운 용어 없이 이해하기 쉽게 설명하는 것이 목표입니다.
정보의 비대칭 해소가 컨셉이며, **종목 추천 기능이 아닙니다** — 입력한 종목 하나만 깊게 분석합니다.

---

## 🏗️ 아키텍처

컴포넌트 3개가 **각자 독립 실행**됩니다. 각 폴더가 자기 `.env` / `requirements.txt`를
가지므로, 백엔드·프론트·MCP 서버·DB(도커)를 **서로 다른 컴퓨터에서 나눠 돌릴 수 있습니다.**

```
[frontend]  ──HTTP──▶  [backend]  ──MCP──▶  [mcp_server]
 Streamlit              FastAPI               stock_mcp (:8050)
                           │                     │
                           └──────┬──────────────┘
                                  ▼
                        [PostgreSQL + pgvector]
```

---

## 📁 폴더 구조

```
stock_insight/
│
├── backend/                        # 🔧 FastAPI 분석 API 서버
│   ├── .env.example                #    환경변수 템플릿 (복사해서 .env 만들기)
│   ├── requirements.txt            #    backend 전용 의존성
│   ├── app/
│   │   ├── main.py                 #    FastAPI 진입점 (uvicorn 실행 대상)
│   │   ├── core/                   #    설정·DB 커넥션 등 공통 기반
│   │   │   └── config.py           #    .env 로드 (pydantic-settings)
│   │   ├── routers/                #    API 엔드포인트 (예: /analyze/{종목})
│   │   ├── schemas/                #    요청/응답 Pydantic 모델
│   │   ├── services/               #    분석 파이프라인·RAG 검색 로직
│   │   └── clients/                #    외부 API 래퍼 (DART·시세·토스 등)
│   └── scripts/                    #    수집·임베딩 배치 (서버와 별개로 미리 실행)
│                                   #    예정: 뉴스 수집 / 청크 임베딩 / 메모 적재
│
├── frontend/                       # 🖥️ Streamlit UI
│   ├── .env.example                #    BACKEND_URL (백엔드가 딴 컴이면 주소 교체)
│   ├── requirements.txt
│   └── app.py                      #    화면 진입점
│
├── mcp_server/                     # 🔌 MCP 툴 서버
│   └── stock_mcp/
│       ├── .env.example            #    DB 주소·포트 (기본 :8050)
│       ├── requirements.txt
│       ├── stock_server.py         #    서버 진입점 — 툴 등록만 담당
│       └── app/
│           ├── core/               #    설정·의존성
│           ├── clients/            #    외부 API·임베딩·벡터스토어 클라이언트
│           ├── schemas/            #    툴 입출력 모델
│           ├── services/           #    툴 비즈니스 로직
│           └── tools/              #    MCP 툴 정의 (services를 호출)
│
├── db/                             # 🗄️ PostgreSQL + pgvector
│   ├── schema.sql                  #    테이블 정의 (아래 DB 설계 참고)
│   └── seed.sql                    #    데모 시드 (demo 유저 + 삼성전자 + 투자메모 3개)
│
├── .gitignore                      # .env / .venv 등 제외 (⚠️ 실제 키는 절대 커밋 금지)
└── README.md
```

---

## 🗄️ DB 설계 원칙

**"숫자는 일반 테이블, 긴 텍스트만 벡터"**

| 테이블 | 종류 | 용도 |
|---|---|---|
| `users` / `positions` / `transactions` | 정형 | 사용자·보유종목·거래내역 (수량·평단·수익률 계산) |
| `fear_greed_daily` | 정형 | 종목×날짜별 공포탐욕 점수 0~100 (추이·전일대비는 SQL로) |
| `rag_chunks` | 벡터 | 긴 텍스트 근거 저장소 — `doc_type`으로 구분 |

`rag_chunks.doc_type` 종류:
- `user_note` — 사용자 투자 메모·매매일지 (매수근거/우려/매도조건 단위)
- `news` — 뉴스 기사 청크
- `disclosure` — DART 공시 서술형 본문 (위험요인·수시공시 등)
- `community_summary` — 토스 커뮤니티 일단위 분위기 요약
- `report` — 서비스가 생성한 과거 분석 리포트

검색 규칙: **SQL로 먼저 필터링(종목코드·doc_type·user_id) → 그 안에서 벡터 top-k.**
임베딩 모델은 `text-embedding-3-small`(1536차원)로 통일 — 바꾸면 전체 재임베딩 필요.

---

## 🚀 실행 방법

### 0. DB 준비 (PostgreSQL + pgvector, 도커 가능)
```bash
psql "$DATABASE_URL" -f db/schema.sql
psql "$DATABASE_URL" -f db/seed.sql     # 데모 데이터 (선택)
```

### 1. 공통 — 맡은 컴포넌트 폴더로 이동 후
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # 열어서 값 채우기 (DB 주소, API 키 등)
```

### 2. 컴포넌트별 실행
| 컴포넌트 | 위치 | 명령어 | 포트 |
|---|---|---|---|
| backend | `backend/` | `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload` | 8000 |
| frontend | `frontend/` | `streamlit run app.py` | 8501 |
| mcp_server | `mcp_server/stock_mcp/` | `python stock_server.py` | 8050 |

다른 컴퓨터에서 나눠 돌릴 때는 각자 `.env`의 주소만 바꾸면 됩니다.
(예: frontend의 `BACKEND_URL`, backend의 `DATABASE_URL`·`MCP_SERVER_URL`)

---

## 📝 참고

- 폴더 구조는 프로젝트 진행하면서 계속 다듬을 예정입니다.
- `.env`는 절대 커밋하지 마세요 — `.env.example`에 키 이름만 추가하는 방식으로 공유합니다.
