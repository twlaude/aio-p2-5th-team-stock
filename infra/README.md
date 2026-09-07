# infra — 로컬 인프라 (Docker Compose)

PostgreSQL(pgvector 포함)과 Redis를 한 번에 띄웁니다. 배포 서버의 systemd 유닛·자동배포는 `docs/operations/`에 정리되어 있습니다.

```bash
cp .env.example .env            # POSTGRES_DB / POSTGRES_USER / POSTGRES_PASSWORD
docker compose up -d
docker compose ps
```

| 서비스 | 이미지 | 포트 | 비고 |
|---|---|---:|---|
| `postgres` | `pgvector/pgvector:pg16` | 5432 | 첫 볼륨 생성 시 `db/schema.sql` → `db/seed.sql` 자동 적용 |
| `redis` | `redis:7-alpine` | 6379 | 단기 Memory(TTL 30분)와 실황 이벤트 채널 |

볼륨(`postgres_data`, `redis_data`)을 지우면 초기화 SQL이 다시 적용됩니다: `docker compose down -v`.
