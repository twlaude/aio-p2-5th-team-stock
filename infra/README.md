# infra — 로컬 인프라 (Docker Compose)

PostgreSQL(pgvector 포함)과 Redis만 띄웁니다(서비스는 가상환경으로 직접 실행하는 개발 방식). 7개 서비스까지 전부 컨테이너로 띄우는 파일은 저장소 루트의 `compose.yml`(소스 빌드)과 `compose.release.yml`(Docker Hub 이미지)이며, 그때 쓰는 PostgreSQL 이미지 레시피가 이 폴더의 `postgres.Dockerfile`과 `init-disclosure-db.sh`입니다. 서비스를 여러 컴퓨터에 나눠 띄우는 방법과 발표 준비는 `docs/operations/`에 정리되어 있습니다.

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
