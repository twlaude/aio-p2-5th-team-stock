# Memory 적용 가이드

## Memory의 목적

Memory는 모든 대화를 저장하는 기능이 아니다. 종목 분석 개인화에 필요한 사용자 상태와 선호를 안전하게 저장하고, 허용된 값만 선택해서 사용하는 기능이다.

## 프로젝트의 Memory 구분

| 종류 | 예시 | 저장 위치 |
|---|---|---|
| 대화 기록 | 향후 기능을 위한 최근 이용 기록 | PostgreSQL, MVP에서는 사용하지 않음 |
| 단기 상태 | 현재 종목, 현재 단계, 보류된 검색 | Redis TTL |
| 장기 Memory | 투자 성향, 투자 기간, 경험 | PostgreSQL |
| RAG 문서 | 뉴스, 공시, 기업보고서 | PostgreSQL·pgvector 또는 MCP 담당 저장소 |

RAG 문서는 사용자 Memory가 아니다.

## 초기 허용 Memory

```text
risk_profile
investment_horizon
experience_level
preferred_evidence
```

초기에는 위 항목처럼 명확하게 허용한 값만 저장한다. 사용자의 자유 대화에서 모든 내용을 자동으로 Memory로 만들지 않는다.

## 사용 흐름

```text
기업명 또는 종목 코드 검색
  → 인증된 사용자 확인
  → 사용자 Memory 조회
  → 허용된 투자 성향 네 값만 선택
  → 정식 기업 정보와 함께 MCP Client에 전달
  → MCP Client가 나를 위한 확인 포인트 생성
  → 사용한 Memory와 근거 추적
```

## 개인화 원칙

- 공통 종목 분석을 변경하지 않는다.
- 매수·매도 적합도를 계산하지 않는다.
- 사용자의 관점에서 먼저 확인할 항목만 설명한다.
- 사용자가 자신의 Memory를 조회·수정·삭제할 수 있어야 한다.

## 초기 구현 범위

1. Mock 투자 성향
2. PostgreSQL 장기 투자 성향
3. Redis 현재 종목·화면 상태
4. Memory 조회·수정·삭제

별도의 Memory MCP 서버는 초기 필수 범위가 아니다. Backend가 사용자 Memory를 소유하고, MCP Client에는 개인화에 필요한 투자 성향 네 값만 전달한다. MCP Client는 이를 공통 분석과 결합해 `personalized_checkpoints`를 생성한다.
