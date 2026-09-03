# PostgreSQL Infrastructure

PostgreSQL·pgvector Docker 실행 설정과 영구 Volume 설명이 들어갈 위치다.

## 실행

`infra/docker-compose.yml`이 `pgvector/pgvector:pg16` 이미지로 띄우고, 컨테이너 최초 실행 시
`db/schema.sql`(vector 확장 + 테이블), `db/seed.sql`(데모 데이터)을 자동 적용한다.

```bash
cd infra
cp .env.example .env   # 필요하면 계정 정보 변경
docker compose up -d postgres
docker exec -it stock_insight_postgres psql -U postgres -d stock_insight -c "\dt"
```

스키마를 바꿨는데 이미 만들어진 Volume 때문에 반영이 안 되면 `docker compose down -v`로 Volume까지 지우고 다시 올린다(데이터가 날아간다).
