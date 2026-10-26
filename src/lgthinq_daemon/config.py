"""Non-secret local connection settings; PAT belongs exclusively in the vault."""

import json
import os
import tempfile
from pathlib import Path
from uuid import UUID, uuid4

FIELDS = {
    "country",
    "client_id",
    "account",
    "device_index",
    "device_id",
    "endpoint",
    "allow_control",
}


def default_path() -> Path:
    return (
        Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "lgthinq-kde/config.json"
    )


def validate(data: dict) -> dict:
    if not isinstance(data, dict) or set(data) - FIELDS:
        raise ValueError(
            "Configuration accepts only country, client_id, account, "
            "device_index, device_id, endpoint, allow_control; no secrets"
        )
    country = data.get("country", "BR")
    account = data.get("account", "default")
    index = data.get("device_index")
    device_id = data.get("device_id")
    if device_id is not None and (
        not isinstance(device_id, str) or not device_id.strip() or len(device_id) > 512
    ):
        raise ValueError("Invalid device identifier")
    if (
        not isinstance(country, str)
        or len(country) != 2
        or not country.isascii()
        or not country.isalpha()
    ):
        raise ValueError("Country must be a two-letter code")
    if not isinstance(account, str) or not account.strip() or len(account) > 128:
        raise ValueError("Account must be a non-empty vault alias up to 128 characters")
    if index is not None and (type(index) is not int or index < 0):
        raise ValueError("Device index must be a nonnegative integer")
    allow_control = data.get("allow_control", False)
    if type(allow_control) is not bool:
        raise ValueError("allow_control must be a boolean")
    endpoint = data.get("endpoint")
    if endpoint is not None:
        from .remote import validate_url

        if not isinstance(endpoint, str):
            raise ValueError("Endpoint must be a URL string")
        endpoint = validate_url(endpoint)
    client_id = data.get("client_id")
    if not isinstance(client_id, str):
        raise ValueError("Configuration requires a stable client_id UUID")
    UUID(client_id)
    return {
        "country": country.upper(),
        "client_id": client_id,
        "account": account,
        "device_index": index,
        "device_id": device_id,
        "endpoint": endpoint,
        "allow_control": allow_control,
    }


def load(path: Path) -> dict:
    try:
        return validate(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError):
        raise ValueError("Cannot read valid connection configuration") from None


def configure(path: Path, overrides: dict, *, clear_none=False) -> dict:
    """Atomic write on explicit user invocation; preserve the installation UUID."""
    data = load(path) if path.exists() else {"client_id": str(uuid4())}
    if overrides.get("device_id") is not None and overrides.get("device_index") is not None:
        raise ValueError("Select either device ID or discovery index")
    if overrides.get("device_id") is not None:
        data["device_index"] = None
    elif overrides.get("device_index") is not None:
        data["device_id"] = None
    data.update({key: value for key, value in overrides.items() if value is not None or clear_none})
    data = validate(data)
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".config-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(data, stream, indent=2)
            stream.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return data


def resolve(args):
    if args.device_index is not None and args.device is not None:
        raise ValueError("Select either device ID or discovery index")
    if args.simulate and (args.endpoint or args.action == "serve-local"):
        raise ValueError("Simulation cannot use a remote endpoint or the live setup service")
    explicit = args.config is not None
    path = Path(args.config).expanduser() if explicit else default_path()
    if args.action == "configure":
        return args, path
    # Simulation must never inherit a real endpoint, appliance or vault selection.
    data = {} if args.simulate else load(path) if explicit or path.exists() else {}
    index_explicit = args.device_index is not None
    for key in FIELDS:
        if key == "device_id":
            continue
        if key == "device_index" and args.device is not None:
            continue
        if getattr(args, key) is None:
            setattr(args, key, data.get(key))
    args.country = args.country or "BR"
    args.account = args.account or "default"
    # Explicit selections win; a stable saved ID wins over a legacy saved index.
    if args.device is None and not index_explicit:
        args.device = data.get("device_id")
    if args.device is not None:
        args.device_index = None
    return args, path
