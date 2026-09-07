import psycopg
from psycopg import sql
from psycopg.conninfo import make_conninfo
from psycopg.rows import dict_row

from app.core.config import settings
from app.core.db import get_cursor


async def _count_tables(cur) -> list[dict]:
    """현재 커서가 붙은 DB의 public 테이블과 정확한 행 수."""
    await cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename")
    tables = []
    for table in await cur.fetchall():
        name = table["tablename"]
        await cur.execute(sql.SQL("SELECT count(*) AS rows FROM public.{}").format(sql.Identifier(name)))
        tables.append({"name": name, **await cur.fetchone()})
    return tables


async def _other_database_tables(name: str) -> list[dict]:
    """백엔드 풀이 붙은 DB가 아닌 팀 DB는 같은 계정으로 따로 접속해 테이블을 센다."""
    conninfo = make_conninfo(settings.database_url, dbname=name)
    async with await psycopg.AsyncConnection.connect(conninfo, row_factory=dict_row, connect_timeout=3) as conn:
        async with conn.cursor() as cur:
            await cur.execute("SET TRANSACTION READ ONLY")
            return await _count_tables(cur)


async def snapshot() -> tuple[dict, dict]:
    """서버의 팀 DB 현황과 각 팀 DB의 정확한 행 수·분석 실패 기록을 조회한다."""
    async with get_cursor() as cur:
        await cur.execute("SET TRANSACTION READ ONLY")
        await cur.execute("SELECT current_setting('server_version') AS version")
        version = (await cur.fetchone())["version"]
        await cur.execute("""
            SELECT d.datname AS name,
                   round(pg_database_size(d.oid) / 1048576.0, 2)::double precision AS size_mb,
                   (SELECT count(*) FROM pg_stat_activity a WHERE a.datid = d.oid) AS connections
            FROM pg_database d
            -- 같은 서버에 다른 프로젝트 DB도 있으므로 팀 DB(현재 DB + *_team)만 보여준다.
            WHERE NOT d.datistemplate AND (d.datname = current_database() OR d.datname LIKE '%\_team')
            ORDER BY d.datname
        """)
        databases = await cur.fetchall()
        await cur.execute("SELECT current_database() AS name")
        current = (await cur.fetchone())["name"]
        tables = [{"database": current, **table} for table in await _count_tables(cur)]
        for database in databases:
            if database["name"] != current:
                tables += [{"database": database["name"], **table}
                           for table in await _other_database_tables(database["name"])]
        await cur.execute("""
            SELECT count(*) AS total,
                   count(*) FILTER (WHERE requested_at >= now() - interval '24 hours') AS last_24h,
                   round(100.0 * count(*) FILTER (WHERE requested_at >= now() - interval '24 hours'
                                                  AND status = 'success') /
                         nullif(count(*) FILTER (WHERE requested_at >= now() - interval '24 hours'), 0), 1)::double precision
                       AS success_rate_24h,
                   max(requested_at) AS last_requested_at
            FROM analysis_runs
        """)
        analysis = await cur.fetchone()
        await cur.execute("""
            SELECT requested_at, user_id, company_name, stock_code, status, partial_failures
            FROM analysis_runs
            WHERE status != 'success' OR coalesce(partial_failures, '[]'::jsonb) != '[]'::jsonb
            ORDER BY requested_at DESC LIMIT 20
        """)
        recent = await cur.fetchall()
        await cur.execute("""
            SELECT failure->>'service' AS service, count(*) AS count
            FROM analysis_runs
            CROSS JOIN LATERAL jsonb_array_elements(partial_failures) AS failure
            WHERE requested_at >= now() - interval '7 days' AND failure->>'service' IS NOT NULL
            GROUP BY failure->>'service' ORDER BY count DESC, service
        """)
        failures = {"recent": recent, "by_service_7d": await cur.fetchall()}
    return {"ok": True, "error": None, "version": version, "databases": databases,
            "tables": tables, "analysis": analysis}, failures
