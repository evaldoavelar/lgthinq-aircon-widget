"""No file, environment or plaintext fallback for credentials."""

import getpass
import os
import sys


class CredentialError(RuntimeError):
    pass


class Vault:
    service = "lgthinq-kde-widget"

    def __init__(self, backend=None, *, service="lgthinq-kde-widget"):
        self.service = service
        if backend is None:
            try:
                # Select a secure implementation directly; never use Chainer/plaintext.
                import keyring
                from keyring.backends import SecretService, kwallet

                if os.environ.get("PYTHON_KEYRING_BACKEND"):
                    candidates = []
                    backend = keyring.get_keyring()
                else:
                    candidates = [SecretService.Keyring, kwallet.DBusKeyring]
                    backend = None
                for candidate in candidates:
                    try:
                        if candidate.priority > 0:
                            backend = candidate()
                            break
                    except Exception:
                        continue
                if backend is None and not os.environ.get("PYTHON_KEYRING_BACKEND"):
                    # keyring 25 defaults to kwalletd5; KF6 keeps the same wire interface.
                    try:
                        import dbus

                        bus = dbus.SessionBus()
                        names = set(bus.list_names()) | set(bus.list_activatable_names())
                        if "org.kde.kwalletd6" in names:
                            backend = kwallet.DBusKeyring()
                            backend.bus_name = "org.kde.kwalletd6"
                            backend.object_path = "/modules/kwalletd6"
                    except Exception:
                        pass
                if backend is None:
                    raise CredentialError("Credential vault unavailable or locked")
            except ImportError:
                raise CredentialError(
                    "Install credential extra and configure Secret Service/KWallet"
                ) from None
        # Reject chainer/plaintext/fail implementations, even if priority is positive.
        module = type(backend).__module__
        if module not in {"keyring.backends.SecretService", "keyring.backends.kwallet"}:
            raise CredentialError(
                "Select an explicit Secret Service or KWallet keyring backend; "
                "in your terminal run: "
                "export PYTHON_KEYRING_BACKEND=keyring.backends.SecretService.Keyring "
                "(requires an available Secret Service vault)"
            )
        self.backend = backend

    def read(self, account: str) -> str:
        try:
            value = self.backend.get_password(self.service, account)
        except Exception:
            raise CredentialError("Credential vault unavailable or locked") from None
        if not value:
            raise CredentialError("PAT absent; use credential-set in a private terminal")
        return value

    def store_interactive(self, account: str) -> None:
        if not sys.stdin.isatty():
            raise CredentialError("Credential entry requires a private interactive terminal")
        is_api = self.service == "lgthinq-homelab-api"
        token = getpass.getpass("Homelab API key (hidden): " if is_api else "LG PAT (hidden): ")
        if is_api and (len(token) < 32 or not token.isascii() or any(c.isspace() for c in token)):
            raise CredentialError(
                "API key requires at least 32 ASCII characters without whitespace"
            )
        self.store(account, token)

    def store(self, account: str, token: str) -> None:
        """Store a transient UI value; never return the existing secret to a caller."""
        if not isinstance(token, str) or not token.strip() or len(token) > 16384:
            raise CredentialError("Empty PAT")
        try:
            self.backend.set_password(self.service, account, token)
        except Exception:
            raise CredentialError("Cannot store PAT in vault") from None
