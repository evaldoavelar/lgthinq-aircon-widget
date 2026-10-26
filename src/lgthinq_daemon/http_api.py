"""Versioned homelab transport; LG credentials never cross this API."""

import asyncio
import hmac
import ipaddress
import json
import time
from collections.abc import Callable

from aiohttp import web

Token = str | Callable[[], str]


def resolve_token(source: Token) -> str:
    token = source() if callable(source) else source
    if (
        not isinstance(token, str)
        or len(token) < 32
        or not token.isascii()
        or any(c.isspace() for c in token)
    ):
        raise ValueError("API token must be at least 32 ASCII characters without whitespace")
    return token


def loopback(host: str) -> bool:
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return host == "localhost"


def response(data, status=200):
    return web.json_response(
        data,
        status=status,
        dumps=lambda value: json.dumps(value, allow_nan=False),
        headers={"Cache-Control": "no-store"},
    )


def create_app(
    engine, token: Token, *, timeout=30, min_interval=1, allow_insecure_http=False, poll_interval=15
) -> web.Application:
    """Caller owns engine lifecycle until app cleanup, which closes its client."""
    resolve_token(token)
    if timeout <= 0 or min_interval < 0:
        raise ValueError("Invalid API timing")
    busy = False
    last_operation = float("-inf")

    @web.middleware
    async def protect(request, handler):
        peer = request.transport.get_extra_info("peername") if request.transport else None
        if not request.secure and not allow_insecure_http and not (peer and loopback(peer[0])):
            return response({"error": "https_required"}, 403)
        if request.path != "/healthz":
            supplied = request.headers.get("Authorization", "")
            try:
                expected = "Bearer " + resolve_token(token)
            except Exception:
                return response({"error": "authentication_unavailable"}, 503)
            if not hmac.compare_digest(supplied.encode(), expected.encode()):
                return response({"error": "unauthorized"}, 401)
        try:
            return await handler(request)
        except web.HTTPException as exc:
            return response({"error": "request_rejected"}, exc.status)
        except asyncio.CancelledError:
            raise
        except Exception:
            return response({"error": "internal_error"}, 500)

    app = web.Application(middlewares=[protect], client_max_size=16384)

    async def health(request):
        return response({"api_version": 1, "status": "ok"})

    async def snapshot(request):
        return response(engine.snapshot.to_dict())

    async def operation(request):
        nonlocal busy, last_operation
        if busy:
            return response({"error": "busy"}, 409)
        if time.monotonic() - last_operation < min_interval:
            return response({"error": "rate_limited"}, 429)
        key, value = None, None
        if request.path == "/v1/commands":
            try:
                data = await request.json()
                if (
                    not isinstance(data, dict)
                    or set(data) != {"key", "value"}
                    or not isinstance(data["key"], str)
                ):
                    raise ValueError()
                key, value = data["key"], data["value"]
                cap = engine.snapshot.capabilities.get(key)
                if cap is None:
                    raise ValueError()
                cap.validate(value)
            except (ValueError, TypeError):
                return response({"error": "invalid_command"}, 400)
        busy = True
        last_operation = time.monotonic()
        try:
            task = engine.command(key, value) if key is not None else engine.refresh()
            await asyncio.wait_for(task, timeout)
            return response(engine.snapshot.to_dict())
        except TimeoutError:
            return response({"error": "operation_timeout"}, 504)
        except ValueError:
            return response({"error": "invalid_command"}, 400)
        finally:
            busy = False

    stop = asyncio.Event()
    poll_task = None

    async def polling():
        nonlocal busy, last_operation
        delay = poll_interval
        while not stop.is_set():
            if not busy and engine.snapshot.connection != "auth_required":
                busy = True
                last_operation = time.monotonic()
                try:
                    await asyncio.wait_for(engine.refresh(), timeout)
                except TimeoutError:
                    pass
                finally:
                    busy = False
                delay = (
                    poll_interval
                    if engine.snapshot.connection == "connected"
                    else min(900, delay * 2)
                )
            try:
                await asyncio.wait_for(stop.wait(), delay)
            except TimeoutError:
                pass

    async def startup(application):
        nonlocal poll_task
        if poll_interval is not None:
            if poll_interval <= 0:
                raise ValueError("Invalid polling interval")
            poll_task = asyncio.create_task(polling())

    async def cleanup(application):
        stop.set()
        if poll_task:
            poll_task.cancel()
            await asyncio.gather(poll_task, return_exceptions=True)
        close = getattr(engine.client, "close", None)
        if close:
            await close()

    app.router.add_get("/healthz", health)
    app.router.add_get("/v1/snapshot", snapshot)
    app.router.add_post("/v1/refresh", operation)
    app.router.add_post("/v1/commands", operation)
    app.on_startup.append(startup)
    app.on_cleanup.append(cleanup)
    return app


def run_server(
    engine,
    token: Token,
    *,
    host="127.0.0.1",
    port=8765,
    ssl_context=None,
    allow_insecure_http=False,
    **options,
):
    """Foreground only; remote binds require TLS unless deliberately overridden."""
    if not loopback(host) and ssl_context is None and not allow_insecure_http:
        raise ValueError("Non-loopback server requires TLS")
    app = create_app(engine, token, allow_insecure_http=allow_insecure_http, **options)
    web.run_app(
        app,
        host=host,
        port=port,
        ssl_context=ssl_context,
        access_log=None,
        print=None,
        handler_cancellation=True,
    )
