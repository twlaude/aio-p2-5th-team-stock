# db — Backend PostgreSQL 스키마

Backend가 쓰는 DB 한 개의 정의입니다. Disclosure MCP 전용 DB는 `mcp_servers/disclosure_mcp/db/`에 따로 있습니다.

| 파일 | 내용 |
|---|---|
| `schema.sql` | 테이블 4개 — `users`(PBKDF2 해시), `user_profiles`(투자 성향), `analysis_runs`(분석 요청 한 건당 한 행, 부분 실패 포함), `rag_chunks` |
| `seed.sql` | 데모 계정 `demo001`~`demo010` (비밀번호 `Demo1234!`)과 성향 |
| `migrations/` | 이미 만들어진 DB에 적용하는 변경. 날짜 순으로 실행 |

## 적용

`infra/docker-compose.yml`로 처음 볼륨을 만들면 `schema.sql` → `seed.sql`이 자동 적용됩니다. 이미 있는 DB에는 다시 적용되지 않으므로 직접 실행합니다.

```bash
psql "$DATABASE_URL" -f db/schema.sql
psql "$DATABASE_URL" -f db/seed.sql
psql "$DATABASE_URL" -f db/migrations/2026-09-04_align_demo_users.sql
```

시각 컬럼은 전부 `TIMESTAMPTZ`(UTC 저장)이고, 화면 표시에서만 KST로 바꿉니다.
