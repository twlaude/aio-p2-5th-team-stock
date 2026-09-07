# 개발 실행 계획

목표는 실제 증권 서비스 배포가 아니라 수업에서 배운 MCP, Agent Workflow, RAG와 Memory를 하나의 동작하는 발표용 서비스에 연결하는 것이다.

## 1. 현재 상태

2026-09-07 현재 코드 기준입니다. 구현 완료와 운영 배포·시험 범위를 구분합니다. 성찰 코드는 `feat/agent-reflection-eval` 브랜치 기준이며 VPS 배포 체크아웃에는 아직 포함되지 않습니다.

| 영역 | 상태 | 다음 작업 |
|---|---|---|
| 공통 계약 | Schema·연결 문서·계약 테스트 연결 완료 | 필드 변경 시 회귀 검증 |
| 지원 기업 20개 | Snapshot과 Backend 회사명/코드 검증 연결 완료 | 범위 변경 시 Snapshot·계약 동시 검토 |
| Community MCP | 실제 FGI/커뮤니티 조회·집계·Client 연동 완료 | 표본·부분 데이터 한계 유지 |
| Price MCP | KIS 현재가·캐시·일봉 재시도·거래량 기준 구현 완료 | 거래량 기준 누락 관측 |
| News MCP | NAVER 기사 정제·관련도·중복 처리·Client 연동 완료 | 기사 축적 시간 기반 관심 해석 점검 |
| Disclosure MCP | DART 조회·보고서 파싱·pgvector 검색·주요 공시 필터 완료 | 본문 파싱·검색 품질 관측 |
| MCP Client | 기본 6개 병렬 수집·규칙 계산·선택 상세·성찰·API 구현 완료 | 실제 상세 실패 복구 보조 Scenario |
| Backend | 인증·회원가입·성향·Memory·분석·서술 채택·실황 구현 완료 | 운영 실패 포함률 지속 관측 |
| Frontend | React 검색·로그인·공개/회원 근거·개인화·오류 화면 연결 완료 | 사용자 검수와 실행 환경별 회귀 확인 |
| DB·Redis | 분석 이력 저장·성향·최근 검색 TTL·실황 연동 구현 완료 | 데이터 수명·관측 범위 점검 |
| 서비스 Docker | 저장소에 Dockerfile 6개, Disclosure Dockerfile 없음 | 전체 컨테이너 완성을 주장하지 않음; VPS는 systemd 운영 |
| 필수 Agent 산출물 | [설계서](../architecture/agent-architecture.md)·[시험 보고서](../reports/agent-test-report.md)·상태 흐름도 작성 | 문맥 검증 한계·실측 미도달 항목 유지 |

## 2. 개발 시작 전 공통 규칙

1. `shared/CONNECTION_CONTRACT.md`와 담당 계약을 읽는다.
2. 필드 이름과 Tool 이름을 코드에서 임의로 바꾸지 않는다.
3. 각 서비스는 Mock 모드에서 단독 실행 가능하게 만든다.
4. 실제 비밀값은 `.env`에만 둔다.
5. MCP 서버는 사용자 정보나 최종 투자 판단을 다루지 않는다.
6. Source가 없는 내용을 LLM이 채우게 하지 않는다.

## 3. 구현된 개발 단계

아래는 초기 순서의 구현 상태를 현재 코드에 맞춰 정리한 것입니다. 서비스별 초기 Mock에서 실제 API·저장소 연결까지 진행했으며, 운영 위치는 [실행 폴더 문서](../operations/RUNTIME_FOLDERS.md)에 별도로 기록합니다.

### A. Price·News·Disclosure MCP

Community MCP의 구조를 복사하지 말고 구조와 책임 분리 방식을 참고한다.

```text
입력 검증 → Service → 외부 Client/Mock → 계약 응답 → Tool 등록
```

각 담당 서비스는 다음 경로로 구현했습니다.

1. 계약과 같은 Mock 응답
2. Tool 입력 검증 테스트
3. `/health`와 `server.py` 실행
4. 실제 데이터 Client
5. 오류·타임아웃 변환
6. 서비스별 실행 진입점(Disclosure의 Dockerfile은 미포함)

### B. MCP Client

1. 네 MCP URL과 상태 확인
2. 여섯 기본 Tool 병렬 호출(네 MCP 서버)
3. 부분 실패 처리
4. 공통 분석용 입력 축소
5. Luna 구조화 출력
6. 최초 1회 + 후속 최대 3회 Runtime, 제한된 성찰·Trace
7. Backend용 REST API

네 MCP의 실제 결과를 캡처한 20종목 픽스처와 실제 모델 비교 하네스를 갖췄습니다. 시험 때는 MCP를 파일 기반으로 대체하고 Agent만 실제 호출합니다.

### C. Backend

1. 지원 기업 조회·검증
2. 비회원 분석 API
3. 데모 사용자 10명·JWT 로그인·회원가입
4. 투자 성향 조회
5. MCP Client 호출
6. 회원 상세 응답
7. Agent 개인화 채택·실패 시 Backend 규칙 조립
8. PostgreSQL·Redis 연결

### D. Frontend

1. 지원 종목 검색
2. 비회원 공개 결과
3. 상세 클릭 시 로그인 안내
4. JWT 로그인 연결
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

위 순서는 초기 연결 검증 순서입니다. 현재 VPS는 일곱 서비스를 systemd로 실행하며 전체 Docker 기동을 이번 작업에서 검증한 것은 아닙니다.

## 5. 최소 완료 기준

### 발표 필수

- 지원 기업과 미지원 기업 구분
- 삼성전자 포함 지원 종목 검색
- 네 MCP 호출 결과 확인
- 시장 온도와 공통 한 줄 설명
- `왜 이렇게 판단했나요?` 근거 표시
- 데모 사용자별 성향에 따른 개인화 확인 포인트
- 일부 MCP 실패 시 나머지 결과 표시
- 출처와 수집 시각 표시

### 추가 구현 완료 영역

- 실제 회원가입 API(Backend 구현, Frontend 가입 화면 미구현)
- 성향 조회·수정 API, Memory 조회·삭제 API
- 관리자 실황의 최근 검색·분석·부분실패 표시

전체 분석 결과 캐시는 현재 완료 범위로 주장하지 않습니다. Redis의 최근 검색 TTL 상태와 Provider 내부 후속 호출 이력을 결과 캐시와 구분합니다.

## 6. 계약 완료 기준

- Community MCP 실제 응답이 Community 계약 테스트를 통과한다.
- 나머지 세 MCP의 Mock과 실제 응답이 같은 Schema를 사용한다.
- MCP Client 응답이 `shared/contracts/analysis`와 일치한다.
- Backend의 비회원·회원 응답이 `shared/contracts/frontend_backend`와 일치한다.

## 7. LLM 비용 제한

- 모델: `gpt-5.6-luna`
- 뉴스: 중복 제거 후 최대 5건
- 보고서: 관련 구절 최대 5개, 정기/주요 공시 각각 최대 5개
- 커뮤니티: 집계·주제·짧은 대표 근거만 전달
- 구조화 출력과 짧은 길이 제한
- Agent 최초 1회 + 후속 최대 3회, on 성찰 추가 호출 총 2회 이내
- Provider 요청 내 이력 재전송, MCP별 캐시와 Backend 최근 검색 상태 분리
- Runtime의 요청별 토큰 계수(Backend 분석 이력에는 토큰 미저장)

모델·호출 방식은 현재 `mcp_client/app/core/config.py`와 `app/providers/openai.py` 기준입니다. 실제 off/on 결과와 비용 계수의 분모는 [에이전트 시험 결과 보고서](../reports/agent-test-report.md)에 기록합니다.
