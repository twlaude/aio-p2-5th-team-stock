# compose.release.yml의 postgres 이미지 레시피.
# pgvector/pgvector:pg16 위에 초기화 SQL을 구워 넣어, 저장소 파일을 마운트하지 않아도 첫 기동 때 DB가 만들어진다.
#   docker build -f infra/postgres.Dockerfile -t ykw492/team5-postgres:latest .
# 초기화는 볼륨을 처음 만들 때 한 번만 실행된다. 이미 있는 볼륨에는 다시 적용되지 않는다.
FROM pgvector/pgvector:pg16

# 파일명 순서대로 실행된다. 01: backend 스키마, 02: 데모 계정 seed, 03: disclosure 전용 DB 생성+스키마
COPY db/schema.sql /docker-entrypoint-initdb.d/01_schema.sql
COPY db/seed.sql   /docker-entrypoint-initdb.d/02_seed.sql
COPY infra/init-disclosure-db.sh /docker-entrypoint-initdb.d/03_init_disclosure_db.sh
# disclosure 스키마는 initdb 폴더 밖에 둔다. 안에 두면 backend DB에도 같이 적용된다.
COPY mcp_servers/disclosure_mcp/db/schema.sql /opt/initdb/disclosure_schema.sql
