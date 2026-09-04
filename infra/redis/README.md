# Redis Infrastructure

Redis Docker 실행 설정, 포트, TTL과 영구 DB와의 경계 설명이 들어갈 위치다.

## 실행

`infra/docker-compose.yml`이 `redis:7-alpine` 이미지로 띄운다. TTL은 Redis 서버 설정이 아니라
각 서비스(Backend)가 키를 쓸 때 지정한다(`REDIS_TTL_SECONDS`).

```bash
cd infra
docker compose up -d redis
docker exec -it stock_insight_redis redis-cli ping
```
