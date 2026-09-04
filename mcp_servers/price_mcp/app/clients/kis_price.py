from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
from threading import Lock
from typing import Any
from zoneinfo import ZoneInfo

import httpx

from app.core.config import PriceConfig


class KISAPIError(Exception):
    pass


class KISConfigurationError(KISAPIError):
    pass


class KISAPITimeout(KISAPIError):
    pass


class KISAPIUnauthorized(KISAPIError):
    pass


class KISAPIUnavailable(KISAPIError):
    pass


class KISAPINoData(KISAPIError):
    pass


class KISPriceClient:
    def __init__(
        self,
        config: PriceConfig,
        transport: httpx.BaseTransport | None = None,
        now_provider: Callable[[], datetime] | None = None,
    ) -> None:
        self._config = config
        self._client = httpx.Client(timeout=config.timeout_seconds, transport=transport)
        self._now = now_provider or (lambda: datetime.now(timezone.utc))
        self._token: str | None = None
        self._token_expires_at: datetime | None = None
        self._token_lock = Lock()

    def _app_key_fingerprint(self) -> str:
        return sha256((self._config.app_key or "").encode("utf-8")).hexdigest()

    def close(self) -> None:
        self._client.close()

    def _is_token_valid(self) -> bool:
        if not self._token or not self._token_expires_at:
            return False
        return self._token_expires_at > self._now() + timedelta(seconds=60)

    def _load_token_cache(self) -> None:
        path = self._config.token_cache_file
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if payload.get("app_key_fingerprint") != self._app_key_fingerprint():
                raise ValueError("cached token belongs to another app key")
            expires_at = datetime.fromisoformat(payload["expires_at"])
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            self._token = payload["access_token"]
            self._token_expires_at = expires_at.astimezone(timezone.utc)
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
            self._token = None
            self._token_expires_at = None

    def _save_token_cache(self) -> None:
        if not self._token or not self._token_expires_at:
            return
        path: Path = self._config.token_cache_file
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "access_token": self._token,
            "expires_at": self._token_expires_at.isoformat(),
            "app_key_fingerprint": self._app_key_fingerprint(),
        }
        path.write_text(json.dumps(payload), encoding="utf-8")

    def _parse_expiration(self, payload: dict[str, Any]) -> datetime:
        raw_expiration = payload.get("access_token_token_expired")
        if raw_expiration:
            try:
                local_expiration = datetime.strptime(raw_expiration, "%Y-%m-%d %H:%M:%S")
                return local_expiration.replace(tzinfo=ZoneInfo("Asia/Seoul")).astimezone(timezone.utc)
            except (TypeError, ValueError):
                pass

        try:
            expires_in = int(payload.get("expires_in", 86400))
        except (TypeError, ValueError):
            expires_in = 86400
        return self._now() + timedelta(seconds=expires_in)

    def _issue_token(self) -> str:
        if not self._config.credentials_configured:
            raise KISConfigurationError("KIS App Key 또는 App Secret이 설정되지 않았습니다.")

        try:
            response = self._client.post(
                f"{self._config.base_url}{self._config.token_url}",
                headers={"content-type": "application/json"},
                json={
                    "grant_type": "client_credentials",
                    "appkey": self._config.app_key,
                    "appsecret": self._config.app_secret,
                },
            )
        except httpx.TimeoutException as exc:
            raise KISAPITimeout() from exc
        except httpx.HTTPError as exc:
            raise KISAPIUnavailable() from exc

        if response.status_code in {401, 403}:
            raise KISAPIUnauthorized()
        if response.status_code >= 400:
            raise KISAPIUnavailable()
        try:
            payload = response.json()
        except ValueError as exc:
            raise KISAPIUnavailable() from exc

        access_token = payload.get("access_token")
        if not access_token:
            raise KISAPIUnauthorized()
        self._token = str(access_token)
        self._token_expires_at = self._parse_expiration(payload)
        self._save_token_cache()
        return self._token

    def _access_token(self, force_refresh: bool = False) -> str:
        with self._token_lock:
            if force_refresh:
                self._token = None
                self._token_expires_at = None
            if not force_refresh and not self._token:
                self._load_token_cache()
            if self._is_token_valid():
                return self._token or ""
            return self._issue_token()

    @staticmethod
    def _token_expired(payload: dict[str, Any]) -> bool:
        return payload.get("msg_cd") == "EGW00123"

    def _request_quote(self, stock_code: str, access_token: str) -> dict[str, Any]:
        try:
            response = self._client.get(
                f"{self._config.base_url}{self._config.price_url}",
                headers={
                    "content-type": "application/json; charset=utf-8",
                    "authorization": f"Bearer {access_token}",
                    "appkey": self._config.app_key or "",
                    "appsecret": self._config.app_secret or "",
                    "tr_id": self._config.tr_id,
                    "custtype": "P",
                },
                params={
                    "FID_COND_MRKT_DIV_CODE": self._config.market_code,
                    "FID_INPUT_ISCD": stock_code,
                },
            )
        except httpx.TimeoutException as exc:
            raise KISAPITimeout() from exc
        except httpx.HTTPError as exc:
            raise KISAPIUnavailable() from exc

        if response.status_code in {401, 403}:
            raise KISAPIUnauthorized()
        if response.status_code >= 400:
            raise KISAPIUnavailable()
        try:
            return response.json()
        except ValueError as exc:
            raise KISAPIUnavailable() from exc

    def _request_daily_prices(self, stock_code: str, access_token: str) -> dict[str, Any]:
        today = self._now().astimezone(ZoneInfo("Asia/Seoul")).date()
        try:
            response = self._client.get(
                f"{self._config.base_url}{self._config.daily_url}",
                headers={
                    "content-type": "application/json; charset=utf-8",
                    "authorization": f"Bearer {access_token}",
                    "appkey": self._config.app_key or "",
                    "appsecret": self._config.app_secret or "",
                    "tr_id": self._config.daily_tr_id,
                    "custtype": "P",
                },
                params={
                    "FID_COND_MRKT_DIV_CODE": self._config.market_code,
                    "FID_INPUT_ISCD": stock_code,
                    "FID_INPUT_DATE_1": (today - timedelta(days=45)).strftime("%Y%m%d"),
                    "FID_INPUT_DATE_2": today.strftime("%Y%m%d"),
                    "FID_PERIOD_DIV_CODE": "D",
                    "FID_ORG_ADJ_PRC": "0",
                },
            )
        except httpx.TimeoutException as exc:
            raise KISAPITimeout() from exc
        except httpx.HTTPError as exc:
            raise KISAPIUnavailable() from exc

        if response.status_code in {401, 403}:
            raise KISAPIUnauthorized()
        if response.status_code >= 400:
            raise KISAPIUnavailable()
        try:
            return response.json()
        except ValueError as exc:
            raise KISAPIUnavailable() from exc

    def get_quote(self, stock_code: str) -> dict[str, Any]:
        token = self._access_token()
        payload = self._request_quote(stock_code, token)
        if self._token_expired(payload):
            token = self._access_token(force_refresh=True)
            payload = self._request_quote(stock_code, token)

        if payload.get("rt_cd") != "0":
            code = str(payload.get("msg_cd", ""))
            if code.startswith("EGW"):
                raise KISAPIUnauthorized()
            raise KISAPIUnavailable()
        output = payload.get("output")
        if not isinstance(output, dict) or not output.get("stck_prpr"):
            raise KISAPINoData()
        return output

    def get_daily_prices(self, stock_code: str) -> list[dict[str, Any]]:
        token = self._access_token()
        payload = self._request_daily_prices(stock_code, token)
        if self._token_expired(payload):
            token = self._access_token(force_refresh=True)
            payload = self._request_daily_prices(stock_code, token)

        if payload.get("rt_cd") != "0":
            code = str(payload.get("msg_cd", ""))
            if code.startswith("EGW"):
                raise KISAPIUnauthorized()
            raise KISAPIUnavailable()
        output = payload.get("output2")
        if not isinstance(output, list):
            raise KISAPIUnavailable()
        return [row for row in output if isinstance(row, dict)]
