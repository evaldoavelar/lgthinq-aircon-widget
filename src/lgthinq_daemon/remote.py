"""Remote HTTP engine usable by the local D-Bus bridge or a future Windows UI."""

import asyncio
import json
from urllib.parse import urlsplit

import aiohttp

from .http_api import Token, loopback, resolve_token
from .models import Capability, Snapshot


def validate_url(url: str, *, allow_insecure_http=False) -> str:
    parts = urlsplit(url)
    if (
        parts.scheme not in {"http", "https"}
        or not parts.hostname
        or parts.username is not None
        or parts.password is not None
        or parts.query
        or parts.fragment
        or parts.path not in {"", "/"}
    ):
        raise ValueError(
            "Remote URL requires an origin without credentials, path, query or fragment"
        )
    if parts.scheme != "https" and not loopback(parts.hostname) and not allow_insecure_http:
        raise ValueError("Remote URL requires HTTPS; HTTP is allowed only on loopback")
    try:
        parts.port
    except ValueError:
        raise ValueError("Invalid remote port") from None
    return url.rstrip("/")


def parse_snapshot(data):
    if not isinstance(data, dict) or set(data) != set(Snapshot().to_dict()):
        raise ValueError("Invalid remote snapshot")
    if (
        not isinstance(data["connection"], str)
        or not isinstance(data["state"], dict)
        or not isinstance(data["capabilities"], dict)
    ):
        raise ValueError("Invalid remote snapshot fields")
    caps = {}
    for key, raw in data["capabilities"].items():
        if not isinstance(raw, dict) or not isinstance(raw.get("path"), list):
            raise ValueError("Invalid remote capability")
        caps[key] = Capability(**{**raw, "path": tuple(raw["path"])})
    return Snapshot(**{**data, "capabilities": caps})


class RemoteEngine:
    def __init__(self, url: str, token: Token, *, timeout=35, allow_insecure_http=False):
        self.url = validate_url(url, allow_insecure_http=allow_insecure_http)
        resolve_token(token)
        self.token = token
        self.timeout = timeout
        self.snapshot = Snapshot()
        self.client = self  # dbus_service shutdown expects engine.client.close().
        self._session = None
        self._lock = asyncio.Lock()

    async def _request(self, method, path, payload=None):
        if self._session is None:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                trust_env=False,
                cookie_jar=aiohttp.DummyCookieJar(),
            )
        async with self._session.request(
            method,
            self.url + path,
            json=payload,
            headers={"Authorization": "Bearer " + resolve_token(self.token)},
            allow_redirects=False,
        ) as reply:
            if reply.status != 200:
                error = {
                    401: "remote_auth_required",
                    403: "remote_forbidden",
                    409: "remote_busy",
                    429: "remote_rate_limited",
                    504: "remote_timeout",
                }.get(reply.status, "remote_error")
                raise ValueError(error)
            chunks, size = [], 0
            async for chunk in reply.content.iter_chunked(65536):
                size += len(chunk)
                if size > 1048576:
                    raise ValueError("remote_response_too_large")
                chunks.append(chunk)

            def invalid_constant(value):
                raise ValueError("Nonfinite remote JSON")

            return parse_snapshot(json.loads(b"".join(chunks), parse_constant=invalid_constant))

    async def _operate(self, method, path, payload=None):
        async with self._lock:
            self.snapshot.connection = "connecting" if payload is None else "command_pending"
            try:
                self.snapshot = await self._request(method, path, payload)
            except asyncio.CancelledError:
                self.snapshot.connection = "disconnected"
                raise
            except Exception as exc:
                allowed = {
                    "remote_auth_required",
                    "remote_forbidden",
                    "remote_busy",
                    "remote_rate_limited",
                    "remote_timeout",
                    "remote_error",
                    "remote_response_too_large",
                }
                error = (
                    str(exc)
                    if isinstance(exc, ValueError) and str(exc) in allowed
                    else "remote_network_error"
                )
                self.snapshot.connection = (
                    "auth_required" if error == "remote_auth_required" else "error"
                )
                self.snapshot.error = error
            return self.snapshot

    async def refresh(self):
        # Cached server snapshot: clients never multiply LG polling traffic.
        return await self._operate("GET", "/v1/snapshot")

    async def request_refresh(self):
        return await self._operate("POST", "/v1/refresh")

    async def command(self, key, value):
        cap = self.snapshot.capabilities.get(key)
        if cap is None:
            raise ValueError("Unknown capability")
        cap.validate(value)
        return await self._operate("POST", "/v1/commands", {"key": key, "value": value})

    async def close(self):
        if self._session is not None:
            await self._session.close()
            self._session = None
