# Memory 적용 가이드

## 발표에서 보여줄 Memory

이번 프로젝트의 핵심 Memory는 사용자별로 저장된 구조화된 투자 성향이다.

```text
experience_level
risk_profile
investment_horizon
preferred_evidence
```

같은 종목의 공통 분석은 같지만, 로그인한 사용자의 Memory에 따라 `나를 위한 확인 포인트`가 달라지는 장면을 보여준다.

## 저장 위치

| 데이터 | 위치 | 수명 |
|---|---|---|
| 투자 성향 | PostgreSQL `investment_profiles` | 장기 |
| 허용된 추가 Memory | PostgreSQL `user_memories` | 장기 |
| 로그인 전 보류 종목 | Redis | 짧은 TTL |
| 분석 결과 캐시 | Redis | 데이터 기준 시각까지 |
| 기업보고서 임베딩 | PostgreSQL/pgvector | 공용 RAG 데이터 |

기업보고서와 공시는 사용자 Memory가 아니다.

## 사용 흐름

```text
회원 분석 요청
  → 인증된 사용자 ID 확인
  → 투자 성향과 현재 질문에 필요한 Memory 조회
  → MCP Client의 공통 분석과 결합
  → 개인화 확인 포인트 생성
```

MCP Client와 MCP 서버에는 사용자 Memory를 보내지 않는다.

## 안전 규칙

- 비밀번호, Token, API Key, 계좌·카드 정보를 Memory에 저장하지 않는다.
- 자유 대화 전체를 자동으로 장기 Memory로 만들지 않는다.
- 사용자 A의 Memory가 사용자 B의 결과에 섞이지 않도록 모든 조회에 인증된 `user_id` 조건을 사용한다.
- Memory는 매수 적합도나 추천 점수를 만들지 않고 설명의 우선순위에만 사용한다.

## MVP와 후순위

### 발표 필수

- Mock 사용자 10명의 고정 투자 성향 조회
- 사용자별 다른 개인화 확인 포인트
- Redis에 로그인 전 종목을 잠시 보관

### 시간이 남으면

- Memory 조회·수정·삭제 API
- 최근 질문 일부 저장
- 사용자가 직접 입력한 관심 근거 저장

별도의 Memory MCP 서버는 만들지 않는다. Backend가 사용자 Memory를 소유한다.
