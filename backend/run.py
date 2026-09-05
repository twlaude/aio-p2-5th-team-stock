"""로컬 실행 진입점. `uvicorn app.main:app` 대신 이걸로 띄운다.

Windows에서 uvicorn은 서브프로세스 관리 때문에 항상 ProactorEventLoop를 쓰도록
하드코딩되어 있다(`uvicorn.loops.asyncio.asyncio_loop_factory`). psycopg3
비동기 모드는 SelectorEventLoop가 필요해서, `uvicorn.run()`/CLI를 거치면
정책을 아무리 미리 바꿔도 소용없다 — uvicorn이 그 정책을 무시하고 직접
`asyncio.ProactorEventLoop`를 지정해서 루프를 만들기 때문이다.

그래서 이 스크립트는 `uvicorn.run()`을 아예 쓰지 않고, 우리가 직접 만든
SelectorEventLoop 위에서 `Server.serve()`를 돌린다.

Linux/macOS(Docker 배포 포함)는 기본이 이미 Selector 계열이라 이 문제 자체가
없다 — `Dockerfile`은 그대로 `uvicorn app.main:app`을 쓴다.

사용법:
    python run.py
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
