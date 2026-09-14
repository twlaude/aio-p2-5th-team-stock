# Backend 동시성 조사 결과 (2026-09-05)

> **한눈에** — 로컬 mock에서 동시 요청 20/100/300개를 비교했습니다.
> 2026-09-06 async+풀 전환 후, 300개에서 sync보다 약 1.7배 빨랐습니다.
> 풀 없는 async는 더 느렸습니다. 느린 외부 API는 지연 주입으로 확인했습니다.

## 결론

2026-09-05의 `def` 라우터 + sync psycopg2 + 요청당 새 커넥션은 스레드 한도(~40)를 넘으면 지연이 늘었습니다.
수십 요청의 짧은 발표는 급하지 않지만, 트래픽·`live` 데모 증가 시 개선이 필요했습니다.
대안은 `async def`·비동기 DB(asyncpg 또는 psycopg3 async)+풀·`httpx.AsyncClient`·분석 경로의 `redis.asyncio`였습니다.

### 최종 결론

2026-09-06에는 라우터·repositories·clients를 `async def`로 바꾸고 psycopg3 async+풀·`redis.asyncio`·`httpx.AsyncClient`를 적용했습니다.
수십 요청은 비슷하고, 수백 요청·느린 API(`live`)는 async가 유리합니다.
풀링(커넥션 재사용)이 함께 필요하며, 생성한 이벤트 루프가 살아 있을 때 종료 훅에서 `close()`해야 합니다.
누락 시 pytest 루프 변경·프로세스 종료 때 정리가 멈춥니다.

## 배경

당시 라우터는 모두 `async def`가 아닌 `def`였습니다. FastAPI는 AnyIO 스레드풀(기본 약 40개)로 실행합니다.
제한된 thread-per-request(요청당 스레드)입니다. 이전 프로젝트의 동시성 문제를 로컬 재현했습니다.

## 테스트 방법

`backend/scripts/load_test.py`로 `POST /api/v1/analyses`에 회원/비회원 절반씩 동시 요청했습니다.
concurrency(동시 요청 수) 20/100/300, `MCP_CLIENT_MODE=mock`으로 외부 API 없이 Backend만 측정했습니다.
DB/Redis는 `infra/docker-compose.yml`의 로컬 PostgreSQL/Redis입니다.

## 결과

| concurrency | 평균 응답시간 | 최대 응답시간 | 배율(평균 기준) | 500/예외 |
|---:|---:|---:|---:|---|
| 20  | 300~440ms   | ~560ms  | 1x   | 0건 |
| 100 | 980~1280ms  | ~1.7s   | ~3x  | 0건 |
| 300 | 2700~3000ms | ~4.6s   | ~9x  | 0건 |

500/미처리 예외 0건이며, 오류 유도 6종(미지원 기업·로그인 실패·인증 누락·위조 토큰·잘못된 요청 본문·성향 값)은
각 단계에서 기대 코드 401/422/200+`unsupported_company`로 응답했습니다.
종료 직후 `pg_stat_activity`는 관측용 1개만 남았습니다. `app/core/db.py`의 `get_cursor()`가 `finally`에서 `conn.close()`해 누수가 없었습니다.

## 해석

20→100은 요청 5배·지연 ~3배, 100→300은 요청 3배·지연 ~2.3배입니다.
스레드풀이 초과 요청을 대기열에 넣어 오류 대신 거의 선형 지연이 생깁니다.
요청마다 `psycopg2.connect()`를 열어 풀링이 없습니다. 로컬의 짧은 쿼리에서는 드러나지 않았지만,
트래픽·느린 쿼리는 `max_connections`(기본 100)를 압박할 수 있습니다.
mock은 외부 호출 없이 즉시 dict를 반환합니다. NAVER/OpenDART/KIS/OpenAI를 기다리는 live는 스레드 점유·지연·타임아웃 위험이 더 큽니다.

## 후속: async 전환 후 재검증 (2026-09-06)

### 커넥션 풀 재도입 후: sync 대비 확실히 개선

| concurrency | sync (기존) | async + 커넥션 풀(`min=2, max=20`) |
|---:|---:|---:|
| 20 | 300~440ms | 343~358ms |
| 100 | 980~1280ms | 881~1464ms |
| 300 | 2700~3000ms | **1581~1764ms** |

300개에서 async+풀(`min=2, max=20`)은 sync보다 1.7배 빠릅니다.
20~100개는 스레드풀 ~40과 커넥션 풀 20의 한도가 비슷해 차이가 작습니다.
~9x는 sync의 20→300 지연 증가, 1.7배는 같은 300개에서 두 방식의 비교입니다.

### 시행착오: 커넥션 풀 없이 async만 하면 오히려 더 나쁘다

| concurrency | sync (기존) | async, 커넥션 풀 없음 |
|---:|---:|---:|
| 20 | 300~440ms | 1190~1610ms |
| 100 | 980~1280ms | 3110~8340ms |
| 300 | 2700~3000ms | 10770~18030ms |

300개에서 풀 없는 async는 sync보다 3.6~6.7배 느렸습니다.
Docker Desktop+WSL2(Windows)의 PostgreSQL 연결 개설은 실측 30~90ms입니다.
sync 스레드 한도(~40)와 달리 async는 개설 요청을 제한하지 않아 몰렸고, 세마포어도 효과가 작았습니다.

`psycopg_pool.AsyncConnectionPool`은 pytest 루프 변경 때 유지보수 태스크가 멈춰 처음에는 보류했습니다.
원인은 풀 미종료였습니다. FastAPI lifespan shutdown에서 같은 루프가 살아 있을 때 명시적으로 `close()`하고,
`with TestClient(app) as client:`로 각 테스트의 루프 안에서 shutdown을 실행해 해결했습니다.

### 느린 외부 API(live 모드) 상황 검증

mock의 `mcp_client`에 부하시험 전용 `MCP_MOCK_DELAY_SECONDS=1`을 주입했습니다(non-blocking `asyncio.sleep`).

| concurrency | async + 풀, 1초 지연 주입 |
|---:|---:|
| 20 | 1423~1467ms (지연 1초 + 오버헤드 거의 없음) |
| 100 | 1860~2268ms |
| 300 | 3721~5030ms |

sync 전체 코드에 1초 블로킹 지연을 넣는 재현은 되돌리기 부담으로 하지 않았습니다.
스레드풀 ~40이면 300÷40 ≈ 8차례, 최소 8초 이상으로 계산해 async 3.7~5초보다 느릴 것으로 예상했습니다.

DB 없는 최소 실험은 `sync def + time.sleep(1)`과 `async def + asyncio.sleep(1)`을 비교했습니다.
`httpx.AsyncClient`의 기본 연결 상한 100도 풀었습니다.

| concurrency | sync (blocking sleep) | async (non-blocking sleep) |
|---:|---:|---:|
| 40 | 1526ms | 1677ms |
| 80 | 2928ms | 1896ms |
| 150 | 4972ms | 2846ms |
| 300 | 9076ms | 7318ms |
| 500 | 14802ms | 7683ms (약 2배 빠름) |

## 재현 방법

```bash
cd infra && docker compose up -d
cd ../backend && uvicorn app.main:app --port 8000 &
python scripts/load_test.py --concurrency 20
python scripts/load_test.py --concurrency 100
python scripts/load_test.py --concurrency 300
```
