# Database와 Redis 개발 가이드

## 운영 단위

MVP에서는 PostgreSQL/pgvector 한 개와 Redis 한 개를 사용한다. MCP마다 별도 DB 인스턴스를 만들지 않는다.

## PostgreSQL 책임

| 테이블 | 책임 담당 |
|---|---|
| `users` | Backend |
| `investment_profiles` | Backend |
| `user_memories` | Backend |
| `supported_companies` | Backend |
| `source_documents` | Disclosure MCP |
| `rag_chunks` | Disclosure MCP |
| `analysis_runs` | Backend |

뉴스·가격·커뮤니티 원본 전체를 이 DB에 저장하지 않는다.

## Redis 책임

- 로그인 세션 또는 데모 Token 상태
- 상세 로그인 전 보류된 종목
- 동일 데이터 기준 시각의 분석 캐시
- 짧은 요청 상태와 TTL

Redis 데이터가 사라져도 사용자 성향과 기업보고서 임베딩은 PostgreSQL에 남아 있어야 한다.

## Seed

`seed.sql`에는 다음만 들어 있다.

- 투자 성향이 다른 Mock 사용자 10명
- 2026-09-01 기준 지원 기업 20개

Mock 비밀번호는 DB에 평문으로 저장하지 않는다.

## RAG 원칙

1. 최신 연간 사업보고서와 최근 공시를 `source_documents`에 기록한다.
2. 문서를 청킹해 `rag_chunks`에 저장한다.
3. 검색 전 종목 코드와 문서 종류를 SQL로 제한한다.
4. 제한된 범위에서 pgvector 유사도 검색을 수행한다.
5. 임베딩 모델이 바뀌면 해당 문서를 다시 임베딩한다.

## 제외한 데이터

포트폴리오, 보유 수량, 평균 매수가, 매매내역과 주문은 프로젝트 목적과 무관하므로 저장하지 않는다.

## 적용 순서

```text
PostgreSQL/pgvector 시작
→ db/schema.sql
→ db/seed.sql
→ Backend 사용자 조회 확인
→ Disclosure MCP RAG 저장 확인
```
