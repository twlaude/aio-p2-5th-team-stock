"""로컬 실행: python run.py.
Windows의 psycopg 비동기 연결에 필요한 SelectorEventLoop에서 서버를 실행한다.
"""
import asyncio
import sys

import uvicorn


def main() -> None:
    config = uvicorn.Config("app.main:app", host="0.0.0.0", port=8000)
    server = uvicorn.Server(config)

    if sys.platform == "win32":
        loop = asyncio.SelectorEventLoop()
        asyncio.set_event_loop(loop)
    else:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(server.serve())
    finally:
        loop.close()


if __name__ == "__main__":
    main()
