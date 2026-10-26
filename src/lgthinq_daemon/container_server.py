"""Explicit container secret mounts; no vault, environment-token or file fallback."""

import argparse
import asyncio
import json
import logging
import os
import ssl
import stat
from pathlib import Path

from .client import SDKClient
from .config import load
from .engine import Engine
from .http_api import resolve_token, run_server


def read_secret(path: Path) -> str:
    """Read one explicitly mounted regular file without following a final symlink."""
    descriptor = None
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        metadata = os.fstat(descriptor)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or stat.S_IMODE(metadata.st_mode) not in {0o400, 0o600}
            or metadata.st_size > 16384
        ):
            raise ValueError()
        with os.fdopen(descriptor, "rb") as stream:
            descriptor = None
            data = stream.read(16385)
        if len(data) > 16384:
            raise ValueError()
        token = data.decode("ascii").strip()
        if not token or any(character.isspace() for character in token):
            raise ValueError()
        return token
    except (OSError, ValueError, UnicodeError):
        raise ValueError(
            "Secret mount unavailable or invalid; require regular ASCII file mode 0400/0600"
        ) from None
    finally:
        if descriptor is not None:
            os.close(descriptor)


class ContainerClient:
    """Create aiohttp in the server loop; never initialize KWallet or D-Bus."""

    def __init__(self, settings: dict, pat_path=Path("/run/secrets/lg_pat")):
        self.settings = settings
        self.pat_path = pat_path
        self._session = None
        self._sdk = None

    async def _client(self):
        if self._sdk is None:
            from aiohttp import ClientSession
            from thinqconnect.thinq_api import ThinQApi

            token = await asyncio.to_thread(read_secret, self.pat_path)
            self._session = ClientSession()
            logging.getLogger("thinqconnect").setLevel(logging.CRITICAL)
            api = ThinQApi(
                session=self._session,
                access_token=token,
                country_code=self.settings["country"],
                client_id=self.settings["client_id"],
            )
            self._sdk = SDKClient(api, allow_control=self.settings.get("allow_control", False))
        return self._sdk

    async def discover(self):
        return await (await self._client()).discover()

    async def profile(self, device_id):
        return await (await self._client()).profile(device_id)

    async def status(self, device_id):
        return await (await self._client()).status(device_id)

    async def control(self, device_id, payload):
        # Default denial applies before opening secrets or creating a session.
        from .client import BackendError

        if not self.settings.get("allow_control", False):
            raise BackendError("real_control_not_authorized")
        await (await self._client()).control(device_id, payload)

    async def close(self):
        if self._session is not None:
            await self._session.close()
            self._session = None
            self._sdk = None


def tls_context(cert, key):
    if bool(cert) != bool(key):
        raise ValueError("TLS requires both certificate and key")
    if not cert:
        return None
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.load_cert_chain(cert, key)
    return context


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tls-cert")
    parser.add_argument("--tls-key")
    args = parser.parse_args(argv)
    try:
        context = tls_context(args.tls_cert, args.tls_key)
        settings = load(Path("/config/config.json"))
        if settings["device_index"] is None:
            raise ValueError("Container config requires device_index")
        api_token = resolve_token(read_secret(Path("/run/secrets/api_token")))
        client = ContainerClient(settings)
        engine = Engine(
            client,
            None,
            device_index=settings["device_index"],
            allow_control=settings["allow_control"],
        )
        # Without TLS, the published host port MUST remain loopback (legacy proxy mode).
        run_server(
            engine,
            api_token,
            host="0.0.0.0",
            port=8765,
            ssl_context=context,
            allow_insecure_http=context is None,
        )
        return 0
    except Exception:
        # Do not print token values, config contents, SDK exceptions or headers.
        print(json.dumps({"error": "container_start_failed_check_config_and_secret_mounts"}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
