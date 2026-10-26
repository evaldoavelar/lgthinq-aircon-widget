#!/usr/bin/env bash
# Standalone installer: copy this file to the homelab; no repository required.
set -euo pipefail
set +x
# Deployment is a separate gate from registry publication. Keep dormant code below
# for synthetic review; no environment variable or CLI flag grants clearance.
if [[ $# -eq 1 && $1 == --help ]]; then
    echo 'Homelab deployment suspended: see docs/DOCKER_COMPLIANCE.md.'
    echo 'No image download, credential access or installation is available.'
    exit 0
fi
echo 'Homelab deployment suspended: historical image rights and compliance unresolved.' >&2
exit 2
command -v python3 >/dev/null || { echo 'python3 is required; nothing installed.' >&2; exit 1; }
exec python3 -c "$(cat <<'PYTHON'
import argparse
import fcntl
import getpass
import ipaddress
import json
import os
import re
import secrets
import shlex
import shutil
import ssl
import stat
import subprocess
import sys
import tempfile
import time
import urllib.request
import uuid
from pathlib import Path


class InstallError(Exception):
    pass


def run(args, capture=False):
    result = subprocess.run(args, check=False, text=True, capture_output=True)
    if result.returncode:
        raise InstallError(f"{args[0]} failed; output suppressed to protect credentials")
    return result.stdout.strip() if capture else None


def ask(label, default):
    value = input(f"{label} [{default}]: ").strip()
    return value or str(default)


def yes(label):
    return ask(label + " (s/N)", "n").lower() in {"s", "sim", "y", "yes"}


def host_name(value):
    try:
        address = ipaddress.ip_address(value)
    except ValueError:
        if ":" in value or re.fullmatch(r"[0-9.]+", value):
            raise InstallError("Invalid LAN IP") from None
        if len(value) > 253 or not all(
            re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?", label)
            for label in value.split(".")
        ):
            raise InstallError("Invalid DNS name") from None
        if value.lower() == "localhost":
            raise InstallError("Use the LAN name")
        return value.lower(), "DNS"
    if (
        address.is_unspecified
        or address.is_multicast
        or address.is_loopback
        or getattr(address, "scope_id", None)
    ):
        raise InstallError("Use a LAN IP, not loopback, wildcard, multicast or scoped IP")
    return str(address), "IP"


def atomic(path, data, uid=0, mode=0o600):
    descriptor, temporary = tempfile.mkstemp(prefix=".install-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chown(temporary, uid, uid)
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def check_tree(directory):
    allowed = {
        ".install.lock",
        "compose.yaml",
        "config.json",
        "installation.json",
        "KDE.txt",
        "secrets",
        "secrets/lg_pat",
        "secrets/api_token",
        "tls",
        "tls/server.crt",
        "tls/server.key",
        "ca",
        "ca/ca.crt",
        "ca/ca.key",
    }
    for path in directory.rglob("*"):
        relative = str(path.relative_to(directory))
        metadata = path.lstat()
        expected_uid = (
            10001
            if relative.startswith(("secrets", "tls")) or relative in {"config.json", "ca/ca.crt"}
            else 0
        )
        if relative not in allowed or path.is_symlink() or not (path.is_file() or path.is_dir()):
            raise InstallError("Unexpected file or symlink in installation directory")
        if metadata.st_uid != expected_uid or stat.S_IMODE(metadata.st_mode) != (
            0o700 if path.is_dir() else 0o600
        ):
            raise InstallError("Incompatible owner or permissions in installation directory")


def secret_value(path):
    data = path.read_bytes()
    value = data.decode("ascii").strip()
    if not value or len(data) > 16384 or any(c.isspace() for c in value):
        raise InstallError("Invalid secret file")
    return value


def certificates(directory, host, kind, renew):
    ca, tls = directory / "ca", directory / "tls"
    if not (ca / "ca.key").exists() and not (ca / "ca.crt").exists():
        # Work in a private staging directory; a failed OpenSSL command leaves no half pair.
        with tempfile.TemporaryDirectory(dir=directory) as temporary:
            stage = Path(temporary)
            run(
                [
                    "openssl",
                    "req",
                    "-x509",
                    "-newkey",
                    "rsa:3072",
                    "-nodes",
                    "-days",
                    "3650",
                    "-subj",
                    "/CN=LGThinQ Homelab Local CA",
                    "-addext",
                    "basicConstraints=critical,CA:TRUE",
                    "-addext",
                    "keyUsage=critical,keyCertSign,cRLSign",
                    "-keyout",
                    str(stage / "key"),
                    "-out",
                    str(stage / "crt"),
                ]
            )
            atomic(ca / "ca.key", (stage / "key").read_text())
            atomic(ca / "ca.crt", (stage / "crt").read_text(), 10001)
    if not (ca / "ca.key").exists() or not (ca / "ca.crt").exists():
        raise InstallError("Incomplete CA; restore its original certificate/key pair")
    if renew or not (tls / "server.crt").exists() or not (tls / "server.key").exists():
        with tempfile.TemporaryDirectory(dir=directory) as temporary:
            stage = Path(temporary)
            run(
                [
                    "openssl",
                    "req",
                    "-new",
                    "-newkey",
                    "rsa:3072",
                    "-nodes",
                    "-subj",
                    "/CN=LGThinQ Homelab",
                    "-keyout",
                    str(stage / "key"),
                    "-out",
                    str(stage / "csr"),
                ]
            )
            (stage / "extensions").write_text(
                f"basicConstraints=critical,CA:FALSE\nkeyUsage=critical,digitalSignature,keyEncipherment\nextendedKeyUsage=serverAuth\nsubjectAltName={kind}:{host},DNS:localhost,IP:127.0.0.1\n"
            )
            run(
                [
                    "openssl",
                    "x509",
                    "-req",
                    "-in",
                    str(stage / "csr"),
                    "-CA",
                    str(ca / "ca.crt"),
                    "-CAkey",
                    str(ca / "ca.key"),
                    "-set_serial",
                    str(secrets.randbits(128)),
                    "-days",
                    "365",
                    "-sha256",
                    "-extfile",
                    str(stage / "extensions"),
                    "-out",
                    str(stage / "crt"),
                ]
            )
            atomic(tls / "server.key", (stage / "key").read_text(), 10001)
            atomic(tls / "server.crt", (stage / "crt").read_text(), 10001)
    run(["openssl", "verify", "-CAfile", str(ca / "ca.crt"), str(tls / "server.crt")])
    run(["openssl", "x509", "-checkend", "0", "-noout", "-in", str(tls / "server.crt")])
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(tls / "server.crt", tls / "server.key")


def guide(endpoint, directory):
    command = "docker compose -f " + shlex.quote(str(directory / "compose.yaml"))
    return f"""LG ThinQ AirCon Widget — conexão KDE
Endpoint: {endpoint}

No home lab, copie SOMENTE {directory}/ca/ca.crt para o computador KDE.
Nunca copie ca.key, server.key ou o PAT. O certificado público também é privado
por padrão no host; use seu acesso administrativo para copiá-lo.

No KDE, salve o certificado como ~/.config/lgthinq-kde/homelab-ca.crt.
Na pasta do projeto (ajuste o caminho se necessário):
  mkdir -p "$HOME/.config/lgthinq-kde"
  cd "$HOME/Documents/lgthinq-aircon-widget"
  export SSL_CERT_FILE="$HOME/.config/lgthinq-kde/homelab-ca.crt"
  export PYTHON_KEYRING_BACKEND=keyring.backends.SecretService.Keyring
  .venv-runtime/bin/python -m lgthinq_daemon api-credential-set
  .venv-runtime/bin/python -m lgthinq_daemon --endpoint {endpoint} configure
  .venv-runtime/bin/python -m lgthinq_daemon status
  .venv-runtime/bin/python -m lgthinq_daemon serve
Cadastre o TOKEN DA API no prompt oculto, nunca o PAT LG.
O certificado é obrigatório em todo terminal que iniciar a ponte; não use -k.
Confira connection/error; /healthz confirma apenas que o processo está vivo.
Pare um backend local anterior antes de iniciar a ponte.

Widget (outro terminal, mesma pasta):
  python3 scripts/prepare_deploy.py --output dist/local \\
    --python "$PWD/.venv-runtime/bin/python" \\
    --config "$HOME/.config/lgthinq-kde/config.json"
  plasma_root="${{XDG_DATA_HOME:-$HOME/.local/share}}/plasma/plasmoids"
  kpackagetool6 --type Plasma/Applet --packageroot "$plasma_root" --list
Se org.lgthinq.aircon estiver ausente, use:
  kpackagetool6 --type Plasma/Applet --packageroot "$plasma_root" \\
    --install "$PWD/dist/local/lgthinq.plasmoid"
Se já estiver instalado, use --upgrade no lugar de --install.
Clique com o botão direito na barra → Adicionar widgets → LG ThinQ AirCon Widget.
O widget usa D-Bus da ponte; IP/porta ficam no endpoint e o token no cofre.

Ponte permanente opcional, APÓS validar em primeiro plano:
Copie dist/local/lgthinq.service para ~/.config/systemd/user/lgthinq.service.
Adicione em [Service] (use caminho absoluto do seu usuário):
  Environment=SSL_CERT_FILE=/CAMINHO/ABSOLUTO/.config/lgthinq-kde/homelab-ca.crt
Pare a ponte em primeiro plano antes de executar:
  systemctl --user daemon-reload
  systemctl --user enable --now lgthinq.service
Não execute essas etapas como root no KDE. Não é preciso reiniciar o Plasma
para mudar apenas a conexão.

No home lab:
  {command} ps
  {command} stop
  {command} start
  {command} restart
  {command} down
Down preserva os arquivos e segredos. Para atualizar a imagem, execute novamente
o instalador com --image localhost/lgthinq:latest e o mesmo --directory.
Para renovar o certificado anual, use --renew-cert com o mesmo diretório;
a CA e o token são preservados. Se mudar o IP/nome, use também --renew-cert.
Para copiar o token ao cofre KDE, execute o instalador com --show-token.
Não publique a porta na internet; permita no firewall somente seus clientes LAN.
"""


def installation_directory(path):
    directory = path.absolute()
    if any(part in {".."} for part in directory.parts) or any(
        c in str(directory) for c in "$\n\r\x00"
    ):
        raise InstallError("Invalid installation path")
    for part in [directory, *directory.parents]:
        if part.is_symlink():
            raise InstallError("Symlink in installation path")
        if part.exists() and (
            not part.is_dir() or part.stat().st_uid != 0 or part.stat().st_mode & 0o022
        ):
            raise InstallError("Installation path requires root-owned, non-writable ancestors")
    if not directory.parent.is_dir():
        raise InstallError("Installation parent must already exist")
    if directory.exists():
        if stat.S_IMODE(directory.stat().st_mode) != 0o700:
            raise InstallError("Existing installation directory requires mode 0700")
        check_tree(directory)
    else:
        directory.mkdir(mode=0o700)
    return directory


def main():
    parser = argparse.ArgumentParser(
        description="Instala LG ThinQ AirCon Widget HTTPS em Docker Linux amd64 (root)."
    )
    parser.add_argument("--directory", type=Path, default=Path("/opt/lgthinq"))
    parser.add_argument("--image", default="localhost/lgthinq:latest")
    parser.add_argument("--renew-cert", action="store_true")
    parser.add_argument(
        "--show-token", action="store_true", help="mostra token API somente no terminal privado"
    )
    args = parser.parse_args()
    if os.geteuid() != 0:
        raise InstallError("Execute como root no home lab; nenhum sudo é executado pelo script")
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        raise InstallError("Use um terminal privado interativo, sem pipe ou captura de saída")
    os.umask(0o077)
    directory = installation_directory(args.directory)
    with (directory / ".install.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if args.show_token:
            token = secret_value(directory / "secrets/api_token")
            print("Token API (não é o PAT LG): " + token)
            return
        for tool in ["docker", "openssl"]:
            if not shutil.which(tool):
                raise InstallError(f"{tool} is required; nothing installed automatically")
        run(["docker", "info"])
        info = json.loads(run(["docker", "info", "--format", "{{json .}}"], True))
        if (
            info.get("OSType") != "linux"
            or info.get("Architecture") not in {"x86_64", "amd64"}
            or any("rootless" in x or "userns" in x for x in info.get("SecurityOptions", []))
        ):
            raise InstallError(
                "Requires conventional Linux amd64 Docker without user namespace remapping"
            )
        run(["docker", "compose", "version"])
        if not re.fullmatch(
            r"localhost/lgthinq(?::[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}|@sha256:[0-9a-f]{64})",
            args.image,
        ):
            raise InstallError("Use a localhost/lgthinq tag or sha256 digest")
        previous = (
            json.loads((directory / "installation.json").read_text())
            if (directory / "installation.json").exists()
            else {}
        )
        if previous and not yes(
            "Reconfigurar/recriar instalação existente preservando os segredos?"
        ):
            print("Instalação preservada.")
            return
        host, kind = host_name(ask("IP ou nome LAN do home lab", previous.get("host", "")))
        port = int(ask("Porta HTTPS", previous.get("port", 8765)))
        if not 1 <= port <= 65535:
            raise InstallError("Port must be 1..65535")
        country = ask("País LG", previous.get("country", "BR")).upper()
        index = int(ask("Índice do aparelho", previous.get("device_index", 0)))
        if not re.fullmatch("[A-Z]{2}", country) or index < 0:
            raise InstallError("Invalid country or device index")
        control = yes("Permitir comandos reais ao aparelho?")
        if previous.get("host", host) != host and not args.renew_cert:
            raise InstallError("IP/name changed; rerun with --renew-cert")
        print("Baixando imagem publicada: " + args.image)
        run(["docker", "pull", args.image])
        digests = json.loads(
            run(
                ["docker", "image", "inspect", "--format", "{{json .RepoDigests}}", args.image],
                True,
            )
        )
        image = next(
            (d for d in digests if re.fullmatch(r"localhost/lgthinq@sha256:[0-9a-f]{64}", d)),
            None,
        )
        if not image:
            raise InstallError("Published image digest unavailable")
        for name, uid in [("secrets", 10001), ("tls", 10001), ("ca", 0)]:
            path = directory / name
            path.mkdir(mode=0o700, exist_ok=True)
            os.chown(path, uid, uid)
        pat = directory / "secrets/lg_pat"
        if not pat.exists():
            print("PAT será salvo explicitamente em arquivo 0600 no host; isso não é um cofre.")
            if not yes("Continuar com secrets de arquivo montados no container?"):
                raise InstallError("Provisionamento cancelado antes de solicitar o PAT")
            value = getpass.getpass("LG PAT (oculto): ", stream=sys.stdout).strip()
            if (
                not value
                or not value.isascii()
                or len(value) > 16384
                or any(c.isspace() for c in value)
            ):
                raise InstallError("Invalid PAT")
            atomic(pat, value + "\n", 10001)
            del value
        secret_value(pat)
        token = directory / "secrets/api_token"
        if not token.exists():
            atomic(token, secrets.token_urlsafe(48) + "\n", 10001)
        if len(secret_value(token)) < 32:
            raise InstallError("API token must have at least 32 characters")
        print("Preparando/verificando certificado HTTPS local...")
        certificates(directory, host, kind, args.renew_cert)
        settings = {
            "country": country,
            "client_id": previous.get("client_id", str(uuid.uuid4())),
            "account": "default",
            "device_index": index,
            "endpoint": None,
            "allow_control": control,
        }
        # Validate preserved UUID rather than silently changing identity.
        uuid.UUID(settings["client_id"])
        atomic(directory / "config.json", json.dumps(settings, indent=2) + "\n", 10001)
        endpoint = f"https://[{host}]:{port}" if ":" in host else f"https://{host}:{port}"
        health = "import ssl,urllib.request; urllib.request.urlopen('https://localhost:8765/healthz',context=ssl.create_default_context(cafile='/tls/ca.crt'),timeout=3).read()"
        manifest = {
            "name": "lgthinq",
            "services": {
                "lgthinq": {
                    "image": image,
                    "platform": "linux/amd64",
                    "command": ["--tls-cert", "/tls/server.crt", "--tls-key", "/tls/server.key"],
                    "ports": [f"{port}:8765"],
                    "restart": "unless-stopped",
                    "read_only": True,
                    "security_opt": ["no-new-privileges:true"],
                    "cap_drop": ["ALL"],
                    "volumes": [
                        {
                            "type": "bind",
                            "source": str(directory / source),
                            "target": target,
                            "read_only": True,
                        }
                        for source, target in [
                            ("config.json", "/config/config.json"),
                            ("tls/server.crt", "/tls/server.crt"),
                            ("tls/server.key", "/tls/server.key"),
                            ("ca/ca.crt", "/tls/ca.crt"),
                        ]
                    ],
                    "secrets": ["lg_pat", "api_token"],
                    "healthcheck": {
                        "test": ["CMD", "python", "-c", health],
                        "interval": "30s",
                        "timeout": "5s",
                        "start_period": "30s",
                    },
                }
            },
            "secrets": {
                name: {"file": str(directory / "secrets" / name)}
                for name in ["lg_pat", "api_token"]
            },
        }
        compose = directory / "compose.yaml"
        atomic(compose, json.dumps(manifest, indent=2) + "\n")
        compose_command = ["docker", "compose", "-f", str(compose)]
        run(compose_command + ["config", "--quiet"])
        metadata = {**settings, "host": host, "port": port, "image": image}
        atomic(directory / "installation.json", json.dumps(metadata, indent=2) + "\n")
        instructions = guide(endpoint, directory)
        atomic(directory / "KDE.txt", instructions)
        print("Iniciando container; validando HTTPS e autenticação...")
        run(compose_command + ["up", "-d", "--force-recreate"])
        # Validate TLS on host loopback, independent of LAN DNS/hairpin routing.
        context = ssl.create_default_context(cafile=str(directory / "ca/ca.crt"))
        opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({}), urllib.request.HTTPSHandler(context=context)
        )
        for attempt in range(30):
            try:
                with opener.open(f"https://localhost:{port}/healthz", timeout=3) as response:
                    if json.load(response).get("status") != "ok":
                        raise InstallError("Invalid health response")
                break
            except Exception:
                if attempt == 29:
                    raise InstallError(
                        "HTTPS health check failed; files preserved, inspect docker compose ps"
                    ) from None
                time.sleep(2)
        request = urllib.request.Request(
            f"https://localhost:{port}/v1/snapshot",
            headers={"Authorization": "Bearer " + secret_value(token)},
        )
        with opener.open(request, timeout=10) as response:
            snapshot = json.load(response)
        print(
            "HTTPS/autenticação: OK. Leitura LG: "
            + (
                "conectada"
                if snapshot.get("connection") == "connected"
                else "pendente; confira status no KDE (não é Go operacional)."
            )
        )
        print(instructions)
        print(
            "Validade do certificado: "
            + run(
                ["openssl", "x509", "-noout", "-enddate", "-in", str(directory / "tls/server.crt")],
                True,
            )
        )
        if yes("Mostrar token API neste terminal privado para copiar ao cofre KDE?"):
            print("Token API (não é o PAT LG): " + secret_value(token))
        else:
            print("Token preservado. Use --show-token neste instalador quando quiser copiá-lo.")


if __name__ == "__main__":
    try:
        main()
    except InstallError as error:
        print(str(error) + ". Arquivos preservados.", file=sys.stderr)
        sys.exit(1)
    except (Exception, KeyboardInterrupt):
        # Never include exceptions, SDK data, secret values or subprocess output.
        print(
            "Instalação interrompida. Confira pré-requisitos, entradas, permissões e "
            "docker compose ps; arquivos existentes foram preservados.",
            file=sys.stderr,
        )
        sys.exit(1)
PYTHON
)" "$@"
