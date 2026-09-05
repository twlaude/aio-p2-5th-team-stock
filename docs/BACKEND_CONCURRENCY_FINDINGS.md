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
