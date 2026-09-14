#!/usr/bin/env bash
# postgres 첫 기동 때 03번으로 실행된다(infra/postgres.Dockerfile 참고).
# backend용 기본 DB(POSTGRES_DB)와 별도로 disclosure_mcp 전용 DB를 만들고
# mcp_servers/disclosure_mcp/db/schema.sql을 적용한다.
set -euo pipefail

DISCLOSURE_DB="${DISCLOSURE_POSTGRES_DB:-stock_disclosure}"

echo "[init-disclosure-db] 데이터베이스 생성: $DISCLOSURE_DB"
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    SELECT 'CREATE DATABASE "$DISCLOSURE_DB"'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DISCLOSURE_DB')\gexec
EOSQL

echo "[init-disclosure-db] 스키마 적용: $DISCLOSURE_DB"
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$DISCLOSURE_DB" \
    -f /opt/initdb/disclosure_schema.sql
