# 최종 아키텍처

이 문서는 2026-09-02 회의, 현재 구현된 Community MCP, 팀에서 확정한 연결 계약을 합친 최종 기준이다.

## 1. 서비스 목적

사용자가 지원 종목을 검색하면 가격·뉴스·기업보고서·커뮤니티 데이터를 모아 현재 상황과 그 근거를 설명한다. 서비스는 투자 결정을 대신하지 않는다.

## 2. 전체 흐름

```text
사용자
  → Frontend
  → Backend
      ├─ 지원 기업 확인
      ├─ 비회원/회원 확인
      └─ 회원의 투자 성향·Memory 조회
  → MCP Client
      ├─ 결정적 Workflow
      ├─ Stock Analysis Agent 1개
      └─ 네 MCP 결과 취합·공통 분석
  → Price MCP ─────── 실시간 가격 API
  → News MCP ──────── 최신 뉴스 API
  → Disclosure MCP ── DART + PostgreSQL/pgvector
  → Community MCP ─── 커뮤니티 데이터 서버
```

표준 종목 분석은 Workflow가 네 기본 MCP Tool을 병렬 호출한다. Agent는 기본 결과가 부족할 때 허용된 추가 Tool을 선택하며 최대 3단계에서 종료한다.

## 3. 서비스 책임

### Frontend

- Backend만 호출한다.
- 검색·공개 결과·로그인·상세 근거·개인화 결과를 표시한다.
- API Key, DB 접속정보, 투자 성향 원본을 관리하지 않는다.

### Backend

- 지원 기업 20개를 확인한다.
- Mock 로그인과 사용자 10명을 구분한다.
- 투자 성향과 Memory를 조회한다.
- MCP Client의 공통 분석을 받아 비회원/회원 응답으로 조립한다.
- 회원에게만 개인화 확인 포인트를 생성한다.

### MCP Client

- Backend가 호출하는 통합 서버다.
- Price·News·Disclosure·Community MCP를 발견·호출한다.
- 네 결과를 정규화하고 시장 온도·근거 수준·한 줄 설명을 만든다.
- 사용자 ID, 로그인 토큰, 투자 성향과 장기 Memory를 받지 않는다.
- 외부 원본 데이터 API를 직접 호출하거나 원본을 저장하지 않는다.

### 네 MCP 서버

- 데이터 수집, 검증, 정제와 출처 유지만 담당한다.
- 소스별 짧은 요약은 가능하지만 최종 시장 온도나 사용자 적합도를 판단하지 않는다.
- 서로 직접 호출하지 않는다.
- 사용자 정보를 받지 않는다.

## 4. MCP 공통 구조

Community MCP를 기준 구현으로 사용한다.

```text
각_mcp/
├─ server.py              # FastMCP 생성, Tool 등록, /health
├─ app/
│  ├─ tools/              # 외부에 공개하는 MCP Tool
│  ├─ services/           # 데이터 정제·계산·업무 규칙
│  ├─ clients/            # 외부 API·DB 연결
│  ├─ schemas/            # 입력·출력 형식
│  ├─ core/               # 설정·로그
│  └─ rag/                # Disclosure MCP에만 사용
├─ tests/
├─ .env.example
├─ requirements.txt
├─ Dockerfile             # 실행 코드 완성 후 추가
└─ GUIDE.md
```

`server.py`에는 데이터 처리 로직을 넣지 않는다.

## 5. LLM 사용 위치

### 공통 분석

MCP Client가 네 데이터의 제한된 요약과 근거를 OpenAI `gpt-5.6-luna`에 전달한다. 출력은 정해진 JSON 형식으로 제한한다.

- 공통 한 줄 설명
- 시장 온도 0~100과 라벨
- 공식 근거 확인 수준
- 뉴스·보고서·커뮤니티 요약
- 사용한 출처와 데이터 부족 경고

### 개인화

Backend가 회원의 네 가지 성향 값과 공통 분석만 사용해 다음을 생성한다.

- 개인화 한 줄 설명
- 먼저 확인할 항목 2개
- 주의할 점 1개

공통 분석 결과는 사용자 성향에 따라 바뀌지 않는다.

## 6. 저장소 책임

| 데이터 | 책임 위치 |
|---|---|
| 사용자·투자 성향·장기 Memory | Backend + PostgreSQL |
| 세션·짧은 캐시 | Backend + Redis |
| 기업보고서 원문 메타데이터·임베딩 | Disclosure MCP + PostgreSQL/pgvector |
| 실시간 가격·뉴스 | 원본 API 조회, 필요 시 각 MCP의 짧은 캐시 |
| 커뮤니티 집계 | 외부 커뮤니티 서버, Community MCP는 조회·변환 |
| 지원 기업 Snapshot | `shared/supported_companies.json` |

MVP에서는 MCP마다 별도 PostgreSQL 인스턴스를 만들지 않는다. 하나의 PostgreSQL/pgvector 인스턴스를 사용하되 테이블 책임을 구분한다.

## 7. 화면 접근 수준

```text
비회원 검색
  → 기업명·가격·등락·공통 한 줄 설명
  → 상세 버튼 클릭 시 회원가입 안내

회원 검색
  → 비회원 결과
  → 시장 온도·근거 요약·출처
  → 투자 성향에 맞춘 확인 포인트
```

## 8. 이번 프로젝트에서 하지 않는 것

- 자동 매수·매도 추천
- 목표주가와 수익률 예측
- 상위 20개 밖의 종목 분석
- 종목별 사용자 커뮤니티
- Multi-Agent 구조
- 관리자 페이지
- 실제 증권 주문
- 포트폴리오·매매내역 관리

## 9. 변경 규칙

입출력 필드나 Tool 이름을 바꿀 때는 `shared/contracts/`를 먼저 수정한다. 서비스 구현과 문서는 계약 변경 후 함께 갱신한다.
