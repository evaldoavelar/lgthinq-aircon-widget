"""ThinQ diagnostics and control with explicit operator opt-in."""

import argparse
import asyncio
import json
import logging
from uuid import UUID

from .client import SDKClient, SimulationClient
from .config import configure, resolve
from .credentials import CredentialError, Vault
from .engine import Engine
from .i18n import gettext


def parser():
    p = argparse.ArgumentParser(
        description=gettext("LG ThinQ AirCon Widget diagnostics and control"),
        epilog=gettext(
            "serve-local reads saved connection settings; use configure or the "
            "UI. --no-allow-control enforces read-only for the whole service "
            "session."
        ),
    )
    p.add_argument("--simulate", action="store_true")
    p.add_argument(
        "--allow-control",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=gettext("Allow real device commands from the CLI/widget (default: read-only)"),
    )
    p.add_argument("--endpoint", help=gettext("Homelab HTTPS origin (no LG PAT needed on client)"))
    p.add_argument(
        "--api-token-account", help=gettext("Homelab access-key vault alias (default: default)")
    )
    p.add_argument("--host", help=gettext("HTTP server bind address (default: 127.0.0.1)"))
    p.add_argument("--port", type=int, help=gettext("HTTP server port (default: 8765)"))
    p.add_argument("--tls-cert")
    p.add_argument("--tls-key")
    p.add_argument("--country")
    p.add_argument("--config", help=gettext("Non-secret JSON configuration path"))
    p.add_argument("--client-id", help=gettext("Stable UUID; generate once with python -m uuid"))
    p.add_argument("--account", help=gettext("Local vault entry alias"))
    p.add_argument("--device-index", type=int, help=gettext("Select a discovery index locally"))
    p.add_argument(
        "--device", help=gettext("Exact device ID, never automatically selects among devices")
    )
    p.add_argument(
        "action",
        choices=[
            "discover",
            "status",
            "command",
            "credential-set",
            "serve",
            "configure",
            "serve-http",
            "api-credential-set",
            "serve-local",
        ],
    )
    p.add_argument("key", nargs="?")
    p.add_argument("value", nargs="?", help=gettext("JSON command value"))
    return p


async def run(args):
    if args.action == "serve":
        raise ValueError(gettext("Use --simulate serve; real daemon lifecycle pending validation"))
    if args.action == "api-credential-set":
        Vault(service="lgthinq-homelab-api").store_interactive(args.api_token_account)
        return {"credential": "homelab_key_stored_in_vault"}
    if args.action == "credential-set":
        Vault().store_interactive(args.account)
        return {"credential": "stored_in_vault"}
    if args.action == "command" and not (args.simulate or args.allow_control):
        raise ValueError(
            gettext("Real control disabled: restart with --allow-control to enable device commands")
        )
    if args.endpoint:
        if args.action not in {"status", "command"}:
            raise ValueError(gettext("Remote CLI supports status, command and serve"))
        from .remote import RemoteEngine

        engine = RemoteEngine(
            args.endpoint, lambda: Vault(service="lgthinq-homelab-api").read(args.api_token_account)
        )
        try:
            await engine.refresh()
            if args.action == "command":
                if args.key is None or args.value is None:
                    raise ValueError(gettext("command requires key and JSON value"))
                await engine.command(args.key, json.loads(args.value))
            return engine.snapshot.to_dict()
        finally:
            await engine.close()
    if args.simulate:
        return await operate(SimulationClient(), args)
    if not args.client_id:
        raise ValueError(gettext("--client-id requires a stable UUID"))
    UUID(args.client_id)
    if len(args.country) != 2 or not args.country.isalpha():
        raise ValueError(gettext("Country must be a two-letter code"))
    from aiohttp import ClientSession
    from thinqconnect.thinq_api import ThinQApi

    # Upstream logs may include device identifiers; diagnostics emit normalized data only.
    logging.getLogger("thinqconnect").setLevel(logging.CRITICAL)
    async with ClientSession() as session:
        api = ThinQApi(
            session=session,
            access_token=Vault().read(args.account),
            country_code=args.country.upper(),
            client_id=args.client_id,
        )
        return await operate(SDKClient(api, allow_control=bool(args.allow_control)), args)


async def operate(client, args):
    devices = await client.discover()
    if args.action == "discover":
        # No raw identifiers or aliases in shareable diagnostics.
        return {
            "count": len(devices),
            "devices": [
                {"index": i, "type": d.get("deviceInfo", {}).get("deviceType", "unknown")}
                for i, d in enumerate(devices)
            ],
        }
    device = "synthetic-ac" if args.simulate else args.device
    if args.device_index is not None:
        if args.device or not 0 <= args.device_index < len(devices):
            raise ValueError(gettext("Invalid device selection"))
        device = devices[args.device_index].get("deviceId")
    if not device or not any(d.get("deviceId") == device for d in devices):
        raise ValueError(
            gettext("Device absent or --device not supplied; no compatibility conclusion")
        )
    engine = Engine(client, device, simulated=args.simulate, allow_control=bool(args.allow_control))
    await engine.refresh()
    if args.action == "command":
        if args.key is None or args.value is None:
            raise ValueError(gettext("command requires key and JSON value"))
        await engine.command(args.key, json.loads(args.value))
    return engine.snapshot.to_dict()


def main():
    try:
        explicit = parser().parse_args()
        if explicit.action == "serve-local":
            # Setup owns connection persistence; never silently ignore CLI overrides.
            if explicit.api_token_account is not None:
                raise ValueError(
                    gettext(
                        "serve-local: --api-token-account is unsupported; vault alias is default"
                    )
                )
            if any(
                getattr(explicit, key) is not None
                for key in ("host", "port", "tls_cert", "tls_key")
            ):
                raise ValueError(
                    gettext(
                        "serve-local does not serve HTTP; use serve-http for host/port/TLS options"
                    )
                )
            if explicit.key is not None or explicit.value is not None:
                raise ValueError(gettext("serve-local accepts no command arguments; use command"))
            for key in (
                "country",
                "client_id",
                "account",
                "device",
                "device_index",
                "endpoint",
            ):
                if getattr(explicit, key) is not None:
                    raise ValueError(
                        gettext(
                            "serve-local does not accept --{value0}; use "
                            "configure or the connection UI"
                        ).format(value0=key.replace("_", "-"))
                    )
            if explicit.allow_control is True:
                raise ValueError(
                    gettext("serve-local: enable control in configure or the connection UI")
                )
        control_disabled = explicit.allow_control is False
        args, config_path = resolve(explicit)
        args.api_token_account = args.api_token_account or "default"
        args.host = args.host or "127.0.0.1"
        args.port = 8765 if args.port is None else args.port
        if args.action == "configure":
            configure(
                config_path,
                {
                    "device_id": args.device,
                    **{
                        key: getattr(args, key)
                        for key in (
                            "country",
                            "client_id",
                            "account",
                            "device_index",
                            "endpoint",
                            "allow_control",
                        )
                    },
                },
            )
            print(json.dumps({"configuration": str(config_path), "secrets_stored": False}))
            return 0
        if args.action in {"serve", "serve-http", "serve-local"}:
            from .dbus_service import serve

            if args.action == "serve-local":
                from .local import LocalController

                engine = LocalController(config_path, control_disabled=control_disabled)
            elif args.endpoint:
                if args.action != "serve":
                    raise ValueError(
                        gettext("Endpoint mode runs a local bridge, not a second server")
                    )
                from .remote import RemoteEngine

                engine = RemoteEngine(
                    args.endpoint,
                    lambda: Vault(service="lgthinq-homelab-api").read(args.api_token_account),
                )
            elif args.simulate:
                engine = Engine(SimulationClient(), "synthetic-ac", simulated=True)
            else:
                from .live import LiveClient

                if (not args.device and args.device_index is None) or not args.client_id:
                    raise ValueError(
                        gettext("Live service requires device selection and stable client-id")
                    )
                UUID(args.client_id)
                if len(args.country) != 2 or not args.country.isalpha():
                    raise ValueError(gettext("Country must be a two-letter code"))
                client = LiveClient(
                    account=args.account,
                    country=args.country.upper(),
                    client_id=args.client_id,
                    allow_control=bool(args.allow_control),
                )
                engine = Engine(
                    client,
                    args.device,
                    device_index=args.device_index,
                    allow_control=bool(args.allow_control),
                )
            if args.action == "serve-http":
                import ssl

                from .http_api import run_server

                if bool(args.tls_cert) != bool(args.tls_key):
                    raise ValueError(gettext("TLS certificate and key must be provided together"))
                context = None
                if args.tls_cert:
                    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                    context.minimum_version = ssl.TLSVersion.TLSv1_2
                    context.load_cert_chain(args.tls_cert, args.tls_key)
                run_server(
                    engine,
                    lambda: Vault(service="lgthinq-homelab-api").read(args.api_token_account),
                    host=args.host,
                    port=args.port,
                    ssl_context=context,
                )
            else:
                serve(engine)
            return 0
        result = asyncio.run(run(args))
        print(json.dumps(result, ensure_ascii=False))
        return 1 if result.get("error") else 0
    except (ValueError, CredentialError, ImportError) as exc:
        # No SDK exception text/headers or arbitrary exception representation.
        print(
            json.dumps(
                {
                    "error": str(exc)
                    if not isinstance(exc, ImportError)
                    else gettext("Optional SDK/credential dependency missing")
                }
            )
        )
        return 2
    except Exception as exc:
        category = (
            "session_bus_unavailable"
            if type(exc).__module__.startswith("dbus")
            else "diagnostic_failed"
        )
        print(json.dumps({"error": category}))
        return 1
