"""Disclosure MCP 전용 DB 스키마를 적용한다.

실행: ``python scripts/init_db.py``
"""

from __future__ import annotations

from pathlib import Path
import sys


MCP_ROOT = Path(__file__).resolve().parents[1]
if str(MCP_ROOT) not in sys.path:
    sys.path.insert(0, str(MCP_ROOT))

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict

from app.core.config import get_config
from app.core.errors import ConfigurationError


SCHEMA_PATH = MCP_ROOT / "db" / "schema.sql"


def main() -> None:
    config = get_config()
    if not config.database_url:
        raise ConfigurationError("DATABASE_URL is required to initialize Disclosure MCP DB.")

    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    connection_params = conninfo_to_dict(config.database_url)
    database_name = connection_params.get("dbname") or connection_params.get("database")
    if not database_name:
        raise ConfigurationError("DATABASE_URL must include a database name.")

    maintenance_params = dict(connection_params)
    maintenance_params.pop("database", None)
    maintenance_params["dbname"] = "postgres"
    with psycopg.connect(autocommit=True, **maintenance_params) as connection:
        exists = connection.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s", (database_name,)
        ).fetchone()
        if exists is None:
            connection.execute(
                sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database_name))
            )

    with psycopg.connect(config.database_url) as connection:
        connection.execute(schema_sql)

    print("Disclosure MCP database schema applied.")


if __name__ == "__main__":
    main()
