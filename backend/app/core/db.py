from contextlib import contextmanager

import psycopg2
import psycopg2.extras

from app.core.config import settings


@contextmanager
def get_cursor(commit: bool = False):
    """요청마다 새 연결을 여는 단순한 방식. 트래픽이 늘면 커넥션 풀로 바꾼다."""
    conn = psycopg2.connect(settings.database_url)
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            yield cur
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
