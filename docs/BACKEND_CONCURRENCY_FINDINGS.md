# Backend 동시성 조사 결과 (2026-09-05)

## 배경

Backend 라우터는 전부 `def`(sync)로 작성되어 있고 `async def`가 아니다. FastAPI는 sync 라우터를
자동으로 스레드풀에서 실행한다(AnyIO 기본 스레드 한도 약 40개) — 즉 "제한된 thread-per-request"
구조다. 이전 프로젝트에서 스레드 하나당 요청 하나를 배정하는 방식이 동시성 문제를 냈던 경험이 있어,
같은 문제가 이 구조에도 있는지 로컬에서 직접 재현해 확인했다.

## 테스트 방법

- 도구: `backend/scripts/load_test.py`
- 환경: 로컬, `MCP_CLIENT_MODE=mock`(외부 API 미사용, 순수 backend 로직만 측정)
- DB/Redis: `infra/docker-compose.yml`로 띄운 로컬 PostgreSQL/Redis
- 측정 대상: `POST /api/v1/analyses`를 회원/비회원 절반씩 섞어 동시 발사
- concurrency 20 / 100 / 300 세 단계로 반복 측정

## 결과

| concurrency | 평균 응답시간 | 최대 응답시간 | 배율(평균 기준) | 500/예외 |
|---:|---:|---:|---:|---|
| 20  | 300~440ms   | ~560ms  | 1x   | 0건 |
| 100 | 980~1280ms  | ~1.7s   | ~3x  | 0건 |
| 300 | 2700~3000ms | ~4.6s   | ~9x  | 0건 |

- 세 단계 모두 500 에러나 처리되지 않은 예외는 0건. 에러 유도 요청 6종(미지원 기업, 로그인 실패,
  인증 누락, 위조 토큰, 잘못된 요청 본문, 잘못된 성향 값)도 매 단계 기대한 상태코드
  (401/422/200+`unsupported_company`)로 정확히 응답했다.
- PostgreSQL 커넥션은 각 단계 종료 직후 `pg_stat_activity` 기준 1개(관측용 커넥션 자신)로,
  누수 없이 정상 반납됨을 확인했다(`app/core/db.py`의 `get_cursor()`가 `finally`에서 항상
  `conn.close()`).

## 해석

- **죽지는 않는다. 대신 계속 느려진다.** concurrency가 늘어날수록 평균 응답시간이 거의 선형으로
  증가한다(20→100: 요청 5배·지연 ~3배, 100→300: 요청 3배·지연 ~2.3배). 이는 스레드풀 대기열이
  요청 수에 비례해 길어지고 있다는 뜻이다.
- 500이 안 뜨는 이유는 스레드풀이 초과 요청을 **큐잉으로 흡수**하기 때문이다. 에러로 실패하는 대신
  대기 시간이 늘어나는 형태로 나타난다.
- DB 커넥션 누수는 없지만, `get_cursor()`가 **요청마다 새 `psycopg2.connect()`를 여는** 구조라
  커넥션 풀링이 없다. 이번 테스트(로컬, 짧은 쿼리)에서는 안 드러났지만 트래픽이 늘거나 쿼리가
  느려지면 `max_connections`(기본 100) 압박으로 이어질 수 있는 잠재 요인이다.
- 이번 테스트는 `MCP_CLIENT_MODE=mock`이라 각 요청의 실제 처리 시간이 매우 짧다(외부 API 호출 없이
  즉시 dict 리턴). 실제 배포 환경처럼 `live` 모드로 느린 외부 API(NAVER/OpenDART/KIS/OpenAI)가
  섞이면, 스레드가 훨씬 오래 점유되어 같은 concurrency에서도 지연이 지금보다 훨씬 크게 나타나고
  타임아웃으로 이어질 가능성이 높다.

## 결론

- 현재 구조(`def` 라우터 + sync psycopg2 + 요청당 새 커넥션)는 **동시 요청이 스레드풀 한도(~40)를
  넘으면 지연시간이 요청 수에 비례해 증가**하는 병목을 갖고 있다. 이번 로컬 재현으로 가설이
  확인되었다.
- 근본 해결책은 async 전환이다: 라우터를 `async def`로, DB는 비동기 드라이버(asyncpg 또는
  psycopg3 async) + 커넥션 풀, `mcp_client` 호출은 `httpx.AsyncClient`, Redis는 이미 있는
  `redis.asyncio`를 분석 경로에도 적용.
- 우선순위 판단: 현재 시연/발표 규모(concurrency 수십 단위, 짧은 데모 세션)에서는 즉시 장애로
  이어지지 않으므로 급하지는 않다. 다만 실제 트래픽이나 `live` 모드 데모가 늘어나면 지연시간
  누적이 사용자 체감으로 이어질 수 있어, 다음 개선 우선순위로 추적한다.

## 재현 방법

```bash
cd infra && docker compose up -d
cd ../backend && uvicorn app.main:app --port 8000 &
python scripts/load_test.py --concurrency 20
python scripts/load_test.py --concurrency 100
python scripts/load_test.py --concurrency 300
```

## 후속: async 전환 후 재검증 (2026-09-06)

위 결론에 따라 라우터·repositories·clients를 전부 `async def`로 전환했다
(psycopg3 async + 커넥션 풀, `redis.asyncio`, `httpx.AsyncClient`). 전환 자체가
실제로 개선인지 다시 로컬에서 측정했다.

### 시행착오: 커넥션 풀 없이 async만 하면 오히려 더 나쁘다

처음엔 "요청마다 새 커넥션을 여는" 방식(sync 시절과 동일한 패턴, async로만 바꿈)으로
갔는데, 측정해보니 **sync보다 나빴다**:

| concurrency | sync (기존) | async, 커넥션 풀 없음 |
|---:|---:|---:|
| 20 | 300~440ms | 1190~1610ms |
| 100 | 980~1280ms | 3110~8340ms |
| 300 | 2700~3000ms | 10770~18030ms |

원인: 이 환경(Docker Desktop + WSL2, Windows)에서 PostgreSQL 커넥션 하나 여는 데
30~90ms가 걸린다(직접 측정). sync+스레드풀 시절엔 스레드 한도(~40)가 "동시에 새
커넥션을 여는 시도 수"를 자연히 제한해줬는데, async는 그 제한이 없어서 concurrency가
오르면 Postgres에 커넥션 개설 요청이 그대로 몰렸다. 세마포어로 동시 개설 수를
제한해봐도 크게 나아지지 않았다 — 결국 필요한 건 "매번 새로 열기"가 아니라
"커넥션 재사용(풀링)"이었다.

커넥션 풀(`psycopg_pool.AsyncConnectionPool`)을 처음 시도했을 때는 pytest에서
이벤트 루프가 테스트마다 바뀌는 상황에 풀의 백그라운드 유지보수 태스크가 정리되지
않고 멈추는 버그가 있어 보류했었다. 원인을 좁혀보니, 문제는 "풀을 아예 안 닫는 것"에
있었다 — FastAPI lifespan shutdown 훅에서 풀이 만들어진 바로 그 이벤트 루프가
살아있는 동안 명시적으로 `close()`하도록 고치고, pytest의 `TestClient`도
`with TestClient(app) as client:` 형태로 감싸 각 테스트가 끝날 때 lifespan
shutdown이 그 테스트의 루프 안에서 실행되도록 맞추니 문제가 사라졌다.

### 커넥션 풀 재도입 후: sync 대비 확실히 개선

| concurrency | sync (기존) | async + 커넥션 풀(`min=2, max=20`) |
|---:|---:|---:|
| 20 | 300~440ms | 343~358ms |
| 100 | 980~1280ms | 881~1464ms |
| 300 | 2700~3000ms | **1581~1764ms** |

300에서 sync 대비 배율이 **~9배 → ~1.7배**로 줄었다. 20~100 구간은 두 방식의
동시 처리 한도(스레드풀 ~40 vs 커넥션 풀 20)가 비슷한 급이라 차이가 크지 않았다.

### 느린 외부 API(live 모드) 상황 검증

지금까지 전부 `MCP_CLIENT_MODE=mock`이라 각 요청이 거의 즉시 끝나는 조건이었다.
실제로 문제가 되는 상황(느린 외부 API 대기)을 흉내내기 위해 `mcp_client`에
`MCP_MOCK_DELAY_SECONDS` 부하테스트 전용 지연(non-blocking `asyncio.sleep`)을
추가해 1초로 놓고 재측정했다.

| concurrency | async + 풀, 1초 지연 주입 |
|---:|---:|
| 20 | 1423~1467ms (지연 1초 + 오버헤드 거의 없음) |
| 100 | 1860~2268ms |
| 300 | 3721~5030ms |

sync 버전에 같은 1초 **블로킹** 지연을 넣어 직접 재현하지는 않았다(비교를 위해
whole 코드베이스를 되돌려야 해서). 대신 스레드풀 크기(~40)로 계산하면, 1초씩
블로킹하는 요청 300개는 `300÷40 ≈ 8`번을 순차로 돌아야 해서 최소 8초 이상
걸릴 수밖에 없다 — 지금 async의 3.7~5초보다 확실히 나쁠 것으로 예상된다.

별도로, DB 없이 `sync def + time.sleep(1)` vs `async def + asyncio.sleep(1)`만
비교하는 최소 실험(`httpx.AsyncClient`의 기본 커넥션 상한 100도 풀어서 공정하게
비교)에서도 같은 경향을 확인했다:

| concurrency | sync (blocking sleep) | async (non-blocking sleep) |
|---:|---:|---:|
| 40 | 1526ms | 1677ms |
| 80 | 2928ms | 1896ms |
| 150 | 4972ms | 2846ms |
| 300 | 9076ms | 7318ms |
| 500 | 14802ms | 7683ms (약 2배 빠름) |

### 최종 결론

- 낮은 동시성(수십 단위)에서는 sync와 async가 큰 차이가 없다 — 둘 다 각자의
  동시 처리 한도 안에 있을 때는 비슷하게 동작한다.
- 동시성이 그 한도를 넘거나(수백 단위), 실제로 느린 외부 API가 섞이면(`live` 모드)
  async가 확실히, 그리고 격차가 벌어지는 방향으로 유리하다.
- **async 전환은 커넥션 풀링과 함께여야 의미가 있다.** 풀 없이 매번 새 커넥션을
  여는 async는 sync+스레드풀보다 오히려 나쁠 수 있다(이번에 실측으로 확인).
- 커넥션 풀을 쓸 때는 그 풀이 만들어진 이벤트 루프가 살아있는 동안 명시적으로
  `close()`하는 종료 훅이 반드시 있어야 한다(FastAPI lifespan shutdown 등) —
  안 그러면 루프가 바뀌거나 죽을 때(pytest, 프로세스 종료) 정리 작업이 멈출 수 있다.
