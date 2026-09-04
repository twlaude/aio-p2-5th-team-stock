import json
from datetime import datetime
from typing import Any

from app.clients.redis import client as redis_client
from app.core.db import get_cursor


def save_run(
    request_id: str,
    user_id: str | None,
    company_name: str,
    stock_code: str,
    access_level: str,
    status: str,
    one_line_summary: str,
    sources: list[dict[str, Any]],
    partial_failures: list[dict[str, Any]],
    personalized_checkpoints: dict[str, Any] | None,
    requested_at: datetime,
    collected_at: datetime | None,
) -> None:
    with get_cursor(commit=True) as cur:
        cur.execute(
            """
            INSERT INTO analysis_runs (
                request_id, user_id, company_name, stock_code, access_level, status,
                one_line_summary, sources, partial_failures, personalized_checkpoints,
                requested_at, collected_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (request_id) DO NOTHING
            """,
            (
                request_id,
                user_id,
                company_name,
                stock_code,
                access_level,
                status,
                one_line_summary,
                json.dumps(sources),
                json.dumps(partial_failures),
                json.dumps(personalized_checkpoints) if personalized_checkpoints is not None else None,
                requested_at,
                collected_at,
            ),
        )
    redis_client.publish_event(
        {
            "type": "analysis_run",
            "request_id": request_id,
            "user_id": user_id,
            "company_name": company_name,
            "stock_code": stock_code,
            "access_level": access_level,
            "status": status,
            "partial_failures": partial_failures,
            "requested_at": requested_at,
        }
    )


def list_recent(limit: int = 20) -> list[dict[str, Any]]:
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT request_id, user_id, company_name, stock_code, access_level, status,
                   partial_failures, requested_at, collected_at
            FROM analysis_runs
            ORDER BY requested_at DESC
            LIMIT %s
            """,
            (limit,),
        )
        return [dict(row) for row in cur.fetchall()]
