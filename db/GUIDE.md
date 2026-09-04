# Database와 Redis 가이드

## 역할 구분

### PostgreSQL

- 회원 정보
- 투자 성향
- 장기 Memory
- 대화 세션과 메시지
- 종목 기본정보
- 분석 기록과 사용 근거
- 공시·보고서 원문 메타데이터

### pgvector

- 전자공시와 기업보고서 청크
- 필요할 경우 뉴스 문서 청크

### Redis

- 현재 선택 종목
- 투자 성향 설정 전 보류된 검색
- 현재 분석 ID와 단계
- 최근 대화 일부
- 반복 요청 캐시
- TTL이 있는 임시 상태

Redis 데이터가 사라져도 회원과 장기 Memory는 PostgreSQL에 남아 있어야 한다.

## 확정된 테이블 (`db/schema.sql`)

Backend가 실제로 필요로 하는 범위부터 먼저 확정했다.

```text
users            회원 기본정보 (user_id, username, password_hash, display_name)
user_profiles    장기 Memory. 허용 네 값만 저장 (users와 1:1)
analysis_runs    분석 기록. sources·partial_failures·personalized_checkpoints는
                 MCP Client가 만드는 가변 구조라 JSONB로 저장
rag_chunks       News·Disclosure·Community MCP 공용 벡터 저장소
```

기존에 있던 `positions`·`transactions`·`fear_greed_daily`는 매수·매도 추천이나
포트폴리오 추적을 하지 않기로 한 `plan.md` 방향과 맞지 않아 제거했다.

## 아직 없는 테이블 (후보)

Price MCP·Disclosure MCP 쪽 설계가 정해지면 추가한다.

```text
companies          종목 마스터 (지금은 shared/supported_companies.json을 직접 읽는다)
conversation_sessions / conversation_messages
source_documents   rag_chunks 원문 관리가 필요해지면
```

## 사용자 분리 원칙

- 사용자 Memory 조회에는 인증된 사용자 ID 조건을 반드시 적용한다.
- Frontend 요청 본문의 사용자 ID만 신뢰하지 않는다.
- 사용자 A의 투자 성향이 사용자 B의 응답에 포함되면 안 된다.

## RAG 검색 원칙

전체 벡터를 바로 검색하지 않고 먼저 다음 조건으로 범위를 줄인다.

```text
종목 코드
문서 종류
발행 기간
필요한 경우 사용자 ID
```

그 범위 안에서 관련 청크를 벡터 검색한다.

## 데이터 시간 정보

- 원문 발행 시각
- 데이터 기준 시각
- 시스템 수집 시각
- 분석 생성 시각

네 시간을 가능한 한 구분해서 저장한다.

## 환경변수 계획

```text
DATABASE_URL
POSTGRES_DB
POSTGRES_USER
POSTGRES_PASSWORD
REDIS_URL
REDIS_TTL_SECONDS
```

## 완료 기준

1. 사용자별 투자 성향이 분리된다.
2. Redis 단기 상태와 PostgreSQL 장기 상태가 구분된다.
3. 공시 원문과 청크의 관계를 추적할 수 있다.
4. 분석 결과에서 사용한 출처를 다시 확인할 수 있다.
5. 사용자가 자신의 Memory를 삭제할 수 있다.
