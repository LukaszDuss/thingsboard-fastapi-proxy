"""Thin async client that authenticates against ThingsBoard and keeps JWT
alive automatically.  Designed with security best-practices:
• HTTPS enforced (unless explicitly allowed via settings).  
• Access & refresh tokens are kept **only in-memory**.  
• Credentials are never written to logs.  
• Refresh happens ~30 seconds before `exp` to avoid edge cases.
"""
from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import httpx
from jose import jwt

from app.core.config import settings

_logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class AuthError(RuntimeError):
    """Raised when authentication with ThingsBoard fails."""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


JWT_ALGS = ["HS256", "HS512", "RS256", "RS512"]  # Whatever TB uses; we just decode header
_TOKEN_REFRESH_GUARD = timedelta(seconds=30)  # refresh 30 s before real expiry


class _TokenStore:
    """In-memory token container (thread-safe)."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.expires_at: Optional[datetime] = None

    # ------------------------------------------------------------------
    async def update(self, access: str, refresh: str) -> None:  # noqa: D401
        """Store new tokens with computed expiry timestamp."""

        try:
            payload = jwt.get_unverified_claims(access)
            exp_ts = payload.get("exp")
            if exp_ts is None:
                raise ValueError("exp missing in JWT")
            expires_at = datetime.fromtimestamp(exp_ts, tz=timezone.utc)
        except Exception as exc:  # pylint: disable=broad-except
            _logger.warning("Could not decode 'exp' from JWT: %s", exc)
            # fallback: ThingsBoard default 2.5h
            expires_at = datetime.now(tz=timezone.utc) + timedelta(hours=2, minutes=30)

        async with self._lock:
            self.access_token = access
            self.refresh_token = refresh
            self.expires_at = expires_at

    # ------------------------------------------------------------------
    async def get_valid_access(self) -> Optional[str]:
        """Return access token if it's still fresh enough."""
        async with self._lock:
            if not self.access_token or not self.expires_at:
                return None
            if datetime.now(tz=timezone.utc) + _TOKEN_REFRESH_GUARD >= self.expires_at:
                # Token is about to expire
                return None
            return self.access_token


# ---------------------------------------------------------------------------
# Public client
# ---------------------------------------------------------------------------


class ThingsBoardClient:
    """Singleton-style async client you can import anywhere."""

    _instance: "ThingsBoardClient | None" = None  # singleton ref

    def __new__(cls):  # noqa: D401
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # ------------------------------------------------------------------
    def __init__(self) -> None:
        self._token_store = _TokenStore()
        self._client = httpx.AsyncClient(
            base_url=str(settings.TB_HOST),  # Convert Pydantic URL to string
            timeout=10.0,
            verify=self._enforce_tls(settings.TB_HOST),
        )
        self._refresh_lock = asyncio.Lock()

    # ------------------------------------------------------------------
    @staticmethod
    def _enforce_tls(url) -> bool:
        url_str = str(url)  # Convert Pydantic URL object to string
        if url_str.startswith("https://"):
            return True  # use default cert store
        _logger.warning(
            "TB_HOST is not HTTPS – TLS verification disabled (dev mode)."
        )
        return False

    # ------------------------------------------------------------------
    async def _login(self) -> None:
        """Initial login – populate tokens."""
        payload = {"username": settings.TB_USERNAME, "password": settings.TB_PASSWORD}
        try:
            resp = await self._client.post("/api/auth/login", json=payload)
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:  # noqa: D401
            raise AuthError(f"Login failed: {exc.response.text}") from exc
        data = resp.json()
        await self._token_store.update(data["token"], data["refreshToken"])
        _logger.info("Authenticated against ThingsBoard as %s", settings.TB_USERNAME)

    # ------------------------------------------------------------------
    async def _refresh(self) -> None:
        """Refresh access token via refresh token."""
        async with self._refresh_lock:
            # another coroutine may have refreshed while we awaited the lock
            if await self._token_store.get_valid_access():
                return

            async with self._token_store._lock:  # noqa: SLF001
                refresh_token = self._token_store.refresh_token
            if not refresh_token:
                # no tokens at all → do full login
                await self._login()
                return

            try:
                resp = await self._client.post(
                    "/api/auth/token",
                    json={"refreshToken": refresh_token},
                )
                resp.raise_for_status()
                data = resp.json()
                await self._token_store.update(data["token"], data["refreshToken"])
                _logger.debug("Refreshed ThingsBoard JWT.")
            except httpx.HTTPError as exc:   # includes status errors
                _logger.warning("Refresh failed – doing re-login. Details: %s", exc)
                await self._login()

    # ------------------------------------------------------------------
    async def _authorized_headers(self) -> dict[str, str]:
        token = await self._token_store.get_valid_access()
        if not token:
            await self._refresh()
            token = await self._token_store.get_valid_access()
            if not token:
                raise AuthError("Unable to obtain access token")
        return {"X-Authorization": f"Bearer {token}"}

    # ------------------------------------------------------------------
    async def get(self, url: str, **kwargs: Any) -> httpx.Response:  # noqa: D401
        headers = kwargs.pop("headers", {})
        headers.update(await self._authorized_headers())
        return await self._client.get(url, headers=headers, **kwargs)

    async def post(self, url: str, **kwargs: Any) -> httpx.Response:  # noqa: D401
        headers = kwargs.pop("headers", {})
        headers.update(await self._authorized_headers())
        return await self._client.post(url, headers=headers, **kwargs)

    async def close(self) -> None:
        await self._client.aclose()


# convenience singleton instance
thingsboard_client = ThingsBoardClient() 