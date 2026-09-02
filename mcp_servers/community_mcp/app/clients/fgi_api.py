from typing import Any

import httpx


class FGIAPIError(Exception): pass


class FGIAPITimeout(FGIAPIError): pass


class FGIAPIUnavailable(FGIAPIError): pass


class FGIAPIUnauthorized(FGIAPIError): pass


class CommunityFGIClient:
    def __init__(self, base_url: str, token: str | None, timeout_sec: float, transport: httpx.BaseTransport | None = None) -> None:
        self._token = token
        self._client = httpx.Client(base_url=base_url.rstrip("/"), timeout=timeout_sec, transport=transport)

    def close(self) -> None:
        self._client.close()

    def get_reaction(self, stock_code: str, lookback_days: int, limit: int) -> dict[str, Any]:
        headers = {}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        try:
            response = self._client.get(
                "/reaction",
                params={"stock_code": stock_code, "lookback_days": lookback_days, "limit": limit},
                headers=headers,
            )
        except httpx.TimeoutException as exc:
            raise FGIAPITimeout() from exc
        except httpx.HTTPError as exc:
            raise FGIAPIUnavailable() from exc

        if response.status_code == 401:
            raise FGIAPIUnauthorized()
        if response.status_code >= 400:
            raise FGIAPIUnavailable()
        try:
            return response.json()
        except ValueError as exc:
            raise FGIAPIUnavailable() from exc
