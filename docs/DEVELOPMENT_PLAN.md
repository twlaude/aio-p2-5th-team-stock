# 개발 실행 계획

목표는 실제 증권 서비스 배포가 아니라 수업에서 배운 MCP, Agent Workflow, RAG와 Memory를 하나의 동작하는 발표용 서비스에 연결하는 것이다.

## 1. 현재 상태

| 영역 | 상태 | 다음 작업 |
|---|---|---|
| 공통 계약 | 확정 | 구현과 계약 테스트 연결 |
| 지원 기업 20개 | 데이터 준비 완료 | Backend 검증에 연결 |
| Community MCP | 구현·테스트 완료 | MCP Client 연동 |
| Price MCP | 구조만 준비 | Mock → 실제 API |
| News MCP | 구조만 준비 | Mock → 실제 API |
| Disclosure MCP | 구조만 준비 | Mock → DART/RAG |
| MCP Client | 구조만 준비 | Mock 네 서버 통합 |
| Backend | `/health`만 구현 | 공개 분석·Mock 로그인·개인화 API |
| Frontend | 최소 화면만 구현 | 세 화면과 Backend 연결 |
| DB·Redis | Compose와 초기화 SQL 준비 | 실제 기동·연결 확인 |
| 서비스 Docker | 3개 서비스만 준비 | 나머지는 실행 코드 후 추가 |

## 2. 개발 시작 전 공통 규칙

1. `shared/CONNECTION_CONTRACT.md`와 담당 계약을 읽는다.
2. 필드 이름과 Tool 이름을 코드에서 임의로 바꾸지 않는다.
3. 각 서비스는 Mock 모드에서 단독 실행 가능하게 만든다.
4. 실제 비밀값은 `.env`에만 둔다.
5. MCP 서버는 사용자 정보나 최종 투자 판단을 다루지 않는다.
6. Source가 없는 내용을 LLM이 채우게 하지 않는다.

## 3. 병렬 개발 순서

### A. Price·News·Disclosure MCP

Community MCP의 구조를 복사하지 말고 구조와 책임 분리 방식을 참고한다.

```text
입력 검증 → Service → 외부 Client/Mock → 계약 응답 → Tool 등록
```

각 담당자는 다음 순서로 진행한다.

1. 계약과 같은 Mock 응답
2. Tool 입력 검증 테스트
3. `/health`와 `server.py` 실행
4. 실제 데이터 Client
5. 오류·타임아웃 변환
6. Dockerfile

### B. MCP Client

1. 네 MCP URL과 상태 확인
2. 네 기본 Tool 병렬 호출
3. 부분 실패 처리
4. 공통 분석용 입력 축소
5. Luna 구조화 출력
6. 최대 3단계 Agent Runtime과 Trace
7. Backend용 REST API

Community MCP가 먼저 연결되고 나머지는 Mock으로 대체할 수 있어야 한다.

### C. Backend

1. 지원 기업 조회·검증
2. 비회원 분석 API
3. Mock 사용자 10명 로그인
4. 투자 성향 조회
5. MCP Client 호출
6. 회원 상세 응답
7. Luna 개인화 확인 포인트
8. PostgreSQL·Redis 연결

### D. Frontend

1. 지원 종목 검색
2. 비회원 공개 결과
3. 상세 클릭 시 로그인 안내
4. Mock 로그인
5. 회원 상세 근거와 개인화 표시
6. 오류·부분 성공 표시

## 4. 연결 순서

```text
각 MCP 단독 테스트
→ MCP Client + 네 MCP
→ Backend + MCP Client
→ Frontend + Backend
→ PostgreSQL·Redis
→ 전체 Docker
```

외부 API가 준비되지 않아도 Mock으로 전체 왕복을 먼저 완성한다.

## 5. 최소 완료 기준

### 발표 필수

- 지원 기업과 미지원 기업 구분
- 삼성전자 포함 지원 종목 검색
- 네 MCP 호출 결과 확인
- 시장 온도와 공통 한 줄 설명
- `왜 이렇게 판단했나요?` 근거 표시
- Mock 사용자별 다른 개인화 확인 포인트
- 일부 MCP 실패 시 나머지 결과 표시
- 출처와 수집 시각 표시

### 시간이 남으면

- 실제 회원가입
- Memory 수정·삭제 화면
- 분석 결과 캐시

관리자 화면은 필수 범위가 아니다.

## 6. 계약 완료 기준

- Community MCP 실제 응답이 Community 계약 테스트를 통과한다.
- 나머지 세 MCP의 Mock과 실제 응답이 같은 Schema를 사용한다.
- MCP Client 응답이 `shared/contracts/analysis`와 일치한다.
- Backend의 비회원·회원 응답이 `shared/contracts/frontend_backend`와 일치한다.

## 7. LLM 비용 제한

- 모델: `gpt-5.6-luna`
- 뉴스: 중복 제거 후 최대 5건
- 보고서: 관련 청크 3~5개
- 커뮤니티: 집계·주제·짧은 대표 근거만 전달
- 구조화 출력과 짧은 길이 제한
- Agent 최대 3단계
- 동일 데이터 기준 시각의 결과 캐시
- 요청별 토큰 사용량 기록

OpenAI 공식 문서에서 `gpt-5.6-luna`는 Responses API와 구조화 출력, Function calling을 지원하는 모델로 확인된다.
