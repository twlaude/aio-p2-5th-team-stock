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

    def _headers(self) -> dict[str, str]:
        if not self._token:
            return {}
        return {"Authorization": f"Bearer {self._token}"}

    def close(self) -> None:
        self._client.close()

    def _get_json(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        try:
            response = self._client.get(path, params=params, headers=self._headers())
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

    def get_reaction(self, stock_code: str, lookback_days: int, limit: int) -> dict[str, Any]:
        return self._get_json(
            "/reaction",
            {"stock_code": stock_code, "lookback_days": lookback_days, "limit": limit},
        )

    def get_fgi(self, stock_code: str) -> dict[str, Any]:
        return self._get_json("/fgi", {"stock_code": stock_code})
