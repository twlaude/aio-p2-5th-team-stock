"""로컬 백엔드에 동시 요청 + 의도적 에러를 쏴서 확인하는 스크립트.

VPS가 아니라 로컬(Mock 모드)에서 돌린다 — 외부 API(NAVER/OpenDART/KIS/OpenAI)
쿼터를 안 쓰고, 실제 팀 데모 데이터(analysis_runs)를 어지르지 않는다.

사용법:
    cd infra && docker compose up -d
    cd ../backend && uvicorn app.main:app --port 8000 &
    python scripts/load_test.py
    python scripts/load_test.py --concurrency 50 --base-url http://localhost:8000
"""

import argparse
import asyncio
import sys
import time

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass
from dataclasses import dataclass, field

import httpx

DEMO_ACCOUNTS = [(f"demo{i:03d}", "Demo1234!") for i in range(1, 11)]
VALID_QUERIES = ["삼성전자", "SK하이닉스", "005930", "000660", "삼성SDI"]


@dataclass
class Result:
    label: str
    status_code: int | None
    elapsed_ms: float
    error: str | None = None


@dataclass
class Report:
    results: list[Result] = field(default_factory=list)

    def add(self, result: Result) -> None:
        self.results.append(result)

    def summarize(self) -> None:
        print(f"\n{'=' * 60}\n총 {len(self.results)}건 결과\n{'=' * 60}")
        by_label: dict[str, list[Result]] = {}
        for r in self.results:
            by_label.setdefault(r.label, []).append(r)

        for label, items in by_label.items():
            codes: dict[str, int] = {}
            for item in items:
                key = str(item.status_code) if item.error is None else f"EXC:{item.error}"
                codes[key] = codes.get(key, 0) + 1
            avg_ms = sum(i.elapsed_ms for i in items) / len(items)
            max_ms = max(i.elapsed_ms for i in items)
            print(f"\n[{label}] {len(items)}건 | 평균 {avg_ms:.0f}ms | 최대 {max_ms:.0f}ms")
            for code, count in sorted(codes.items()):
                print(f"    {code}: {count}건")

        unexpected_500s = [r for r in self.results if r.status_code == 500]
        exceptions = [r for r in self.results if r.error is not None]
        print(f"\n{'=' * 60}")
        if unexpected_500s or exceptions:
            print(f"[경고] 500 에러 {len(unexpected_500s)}건, 예외 {len(exceptions)}건 — 로그 확인 필요")
        else:
            print("[OK] 처리 안 된 500/예외 없음")


async def _timed_request(client: httpx.AsyncClient, label: str, report: Report, **kwargs) -> None:
    start = time.perf_counter()
    try:
        response = await client.request(**kwargs)
        elapsed = (time.perf_counter() - start) * 1000
        report.add(Result(label=label, status_code=response.status_code, elapsed_ms=elapsed))
    except httpx.HTTPError as exc:
        elapsed = (time.perf_counter() - start) * 1000
        report.add(Result(label=label, status_code=None, elapsed_ms=elapsed, error=type(exc).__name__))


async def login(client: httpx.AsyncClient, username: str, password: str) -> str | None:
    try:
        response = await client.post("/api/v1/auth/login", json={"username": username, "password": password})
        return response.json().get("access_token") if response.status_code == 200 else None
    except httpx.HTTPError:
        return None


async def concurrent_valid_analyses(client: httpx.AsyncClient, report: Report, n: int) -> None:
    """정상 분석 요청 n개를 동시에 쏜다 (게스트/회원 섞어서)."""
    tokens = await asyncio.gather(*(login(client, u, p) for u, p in DEMO_ACCOUNTS))
    tasks = []
    for i in range(n):
        query = VALID_QUERIES[i % len(VALID_QUERIES)]
        token = tokens[i % len(tokens)] if i % 2 == 0 else None
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        label = "동시 분석 요청(회원)" if token else "동시 분석 요청(비회원)"
        tasks.append(
            _timed_request(
                client, label, report,
                method="POST", url="/api/v1/analyses", json={"query": query}, headers=headers,
            )
        )
    await asyncio.gather(*tasks)


async def intentional_errors(client: httpx.AsyncClient, report: Report) -> None:
    """의도적으로 실패를 유발하는 요청들을 동시에 쏜다."""
    tasks = [
        _timed_request(  # 지원하지 않는 기업 -> 200 + unsupported_company
            client, "미지원 기업", report,
            method="POST", url="/api/v1/analyses", json={"query": "존재하지않는가상회사"},
        ),
        _timed_request(  # 잘못된 비밀번호 -> 401
            client, "로그인 실패", report,
            method="POST", url="/api/v1/auth/login", json={"username": "demo001", "password": "wrong"},
        ),
        _timed_request(  # 인증 없이 보호된 엔드포인트 -> 401
            client, "인증 누락", report,
            method="GET", url="/api/v1/profile",
        ),
        _timed_request(  # 잘못된 토큰 -> 401
            client, "위조 토큰", report,
            method="GET", url="/api/v1/profile", headers={"Authorization": "Bearer not-a-real-token"},
        ),
        _timed_request(  # 필수 필드 누락 -> 422
            client, "잘못된 요청 본문", report,
            method="POST", url="/api/v1/analyses", json={},
        ),
        _timed_request(  # 존재하지 않는 사용자로 회원가입 시도 후 중복 가입 -> 400 유도용 사전 준비는 생략, 잘못된 프로필 값만 검증
            client, "잘못된 성향 값", report,
            method="POST", url="/api/v1/auth/signup",
            json={
                "username": "load_test_bad_profile",
                "password": "SafePass1!",
                "display_name": "부하테스트",
                "profile": {
                    "experience_level": "not-a-real-level",
                    "risk_profile": "balanced",
                    "investment_horizon": "long",
                    "preferred_evidence": "news",
                },
            },
        ),
    ]
    await asyncio.gather(*tasks)


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--concurrency", type=int, default=20, help="동시 분석 요청 개수")
    args = parser.parse_args()

    report = Report()
    # httpx 기본 커넥션 상한(max_connections=100)에 concurrency가 걸리면 서버가 아니라
    # 이 클라이언트 자체가 병목이 된다 — 풀어준다.
    limits = httpx.Limits(max_connections=None, max_keepalive_connections=None)
    async with httpx.AsyncClient(base_url=args.base_url, timeout=30.0, limits=limits) as client:
        try:
            health = await client.get("/health")
            health.raise_for_status()
        except httpx.HTTPError as exc:
            print(f"백엔드({args.base_url})에 연결할 수 없다: {exc}")
            print("먼저 infra(docker compose up -d)와 uvicorn을 띄워라.")
            return

        print(f"백엔드 정상 확인. 동시 분석 요청 {args.concurrency}개 발사...")
        await concurrent_valid_analyses(client, report, args.concurrency)

        print("의도적 에러 유발 요청 발사...")
        await intentional_errors(client, report)

    report.summarize()


if __name__ == "__main__":
    asyncio.run(main())
