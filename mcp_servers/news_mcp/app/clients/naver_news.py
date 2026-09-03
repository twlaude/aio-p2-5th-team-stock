from typing import Any

import httpx


class NaverNewsAPIError(Exception): pass


class NaverNewsAPITimeout(NaverNewsAPIError): pass


class NaverNewsAPIUnavailable(NaverNewsAPIError): pass


class NaverNewsAPIUnauthorized(NaverNewsAPIError): pass


class NaverNewsClient:
    def __init__(
        self,
        base_url: str,
        client_id: str | None,
        client_secret: str | None,
        timeout_sec: float,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._client = httpx.Client(timeout=timeout_sec, transport=transport)
        self._base_url = base_url

    def _headers(self) -> dict[str, str]:
        return {
            "X-Naver-Client-Id": self._client_id or "",
            "X-Naver-Client-Secret": self._client_secret or "",
        }

    def close(self) -> None:
        self._client.close()

    def search_news(self, query: str, display: int) -> dict[str, Any]:
        try:
            response = self._client.get(
                self._base_url,
                params={"query": query, "display": display, "sort": "date"},
                headers=self._headers(),
            )
        except httpx.TimeoutException as exc:
            raise NaverNewsAPITimeout() from exc
        except httpx.HTTPError as exc:
            raise NaverNewsAPIUnavailable() from exc

        if response.status_code == 401:
            raise NaverNewsAPIUnauthorized()
        if response.status_code >= 400:
            raise NaverNewsAPIUnavailable()
        try:
            return response.json()
        except ValueError as exc:
            raise NaverNewsAPIUnavailable() from exc
