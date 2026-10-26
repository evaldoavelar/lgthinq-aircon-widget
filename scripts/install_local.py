#!/usr/bin/env python3
"""Per-user integrated installer. Build a standalone .pyz with build_local.py."""

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path

from package_manifest import BACKEND, backend_catalogs, source_file, sources, validate_archive

try:
    from i18n_support import gettext  # standalone zipapp
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from lgthinq_daemon.i18n import gettext

MARKER = "# Managed by lgthinq-local installer v1"
SERVICE = "org.lgthinq.LGThinq"
UNIT = "lgthinq-local.service"


def run(arguments, **kwargs):
    return subprocess.run(arguments, check=True, **kwargs)


def reload_activation():
    # systemd daemon-reload alone does not refresh the session bus service catalogue.
    run(
        [
            "dbus-send",
            "--session",
            "--type=method_call",
            "--print-reply",
            "--dest=org.freedesktop.DBus",
            "/org/freedesktop/DBus",
            "org.freedesktop.DBus.ReloadConfig",
        ],
        stdout=subprocess.DEVNULL,
    )


def quoted(value, *, systemd=True):
    value = str(value)
    if any(c in value for c in "\n\r\0"):
        raise ValueError(gettext("Unsupported control character in installation path"))
    value = value.replace("\\", "\\\\").replace('"', '\\"')
    if systemd:
        value = value.replace("%", "%%").replace("$", "$$")
    return '"' + value + '"'


class Installer:
    def __init__(self):
        home = Path.home()
        self.data = Path(os.environ.get("XDG_DATA_HOME", home / ".local/share"))
        self.config = Path(os.environ.get("XDG_CONFIG_HOME", home / ".config"))
        if not self.data.is_absolute() or not self.config.is_absolute():
            raise ValueError(gettext("XDG paths must be absolute"))
        self.root = self.data / "lgthinq-local"
        self.current = self.root / "current"
        self.packages = self.data / "plasma/plasmoids"
        self.widget = self.packages / "org.lgthinq.aircon"
        self.activation = self.data / "dbus-1/services/org.lgthinq.LGThinq.service"
        self.unit = self.config / "systemd/user" / UNIT
        self.receipt = self.root / "installation.json"

    def retry_command(self):
        return shlex.join([sys.executable, str(Path(sys.argv[0]).resolve()), "install"])

    def remove_widget_command(self):
        return shlex.join(
            [
                "kpackagetool6",
                "--type",
                "Plasma/Applet",
                "--packageroot",
                str(self.packages),
                "--remove",
                "org.lgthinq.aircon",
            ]
        )

    def preflight(self, *, removing=False):
        if sys.version_info < (3, 11):  # noqa: UP036 - standalone installer runs before pip
            raise ValueError(gettext("Python 3.11 ou superior é necessário"))
        if os.getuid() == 0:
            raise ValueError(gettext("Execute como usuário da sessão KDE, sem sudo/root"))
        if self.root.is_symlink() or (self.root / "releases").is_symlink():
            raise ValueError(gettext("Diretório de instalação simbólico não gerenciado"))
        if self.receipt.exists():
            releases = (self.root / "releases").resolve()
            if not self.current.exists() or not self.current.resolve().is_relative_to(releases):
                raise ValueError(
                    gettext("Recibo local inconsistente; revise a instalação antes de alterar")
                )
        legacy = self.config / "systemd/user/lgthinq.service"
        if legacy.exists():
            raise ValueError(
                gettext(
                    "Foi encontrado o serviço da instalação antiga "
                    "(lgthinq.service).\nPara encerrar esse serviço e impedir que "
                    "volte no próximo login, execute:\n\n  systemctl --user "
                    "disable --now lgthinq.service\n  rm -- {value0}\n  systemctl "
                    "--user daemon-reload\n\nEsses comandos removem apenas o "
                    "serviço antigo, preservando PAT e configurações.\nDepois, "
                    "tente instalar novamente:\n\n  {value1}"
                ).format(value0=shlex.quote(str(legacy)), value1=self.retry_command())
            )
        for command in ["kpackagetool6", "systemctl", "systemd-analyze", "dbus-send"]:
            if not shutil.which(command):
                raise ValueError(
                    gettext(
                        "Dependência ausente: {value0}; instale pelo gerenciador da distribuição"
                    ).format(value0=command)
                )
        run(["systemctl", "--user", "show-environment"], stdout=subprocess.DEVNULL)
        if not removing:
            run(
                [sys.executable, "-c", "import venv, dbus; from gi.repository import GLib"],
                stdout=subprocess.DEVNULL,
            )
            # Match the actual QML interface required by the widget, not merely a version number.
            qmltypes = Path("/usr/lib/qt6/qml/org/kde/plasma/workspace/dbus/dbusplugin.qmltypes")
            candidates = [
                qmltypes,
                Path("/usr/lib64/qt6/qml/org/kde/plasma/workspace/dbus/dbusplugin.qmltypes"),
            ]
            if not any(p.is_file() and "SignalWatcher" in p.read_text() for p in candidates):
                raise ValueError(
                    gettext("Módulo Plasma org.kde.plasma.workspace.dbus com SignalWatcher ausente")
                )
            run(
                [
                    "dbus-send",
                    "--session",
                    "--print-reply",
                    "--dest=org.freedesktop.DBus",
                    "/org/freedesktop/DBus",
                    "org.freedesktop.DBus.GetId",
                ],
                stdout=subprocess.DEVNULL,
            )
        for path in [self.unit, self.activation]:
            if path.is_symlink():
                raise ValueError(
                    gettext("Registro simbólico não gerenciado: {value0}").format(value0=path)
                )
            if path.exists() and MARKER not in path.read_text():
                raise ValueError(
                    gettext(
                        "Arquivo existente não gerenciado: {value0}; migração manual necessária"
                    ).format(value0=path)
                )
        if self.widget.exists() and not self.receipt.exists():
            raise ValueError(
                gettext(
                    "Encontramos uma instalação antiga do widget LG ThinQ AirCon "
                    "Widget.\nNada foi removido. Para substituir pelo produto "
                    "integrado:\n\n1. Remova a instância LG ThinQ AirCon Widget da "
                    "barra pelo modo de edição do painel.\n2. Copie e execute "
                    "este comando no mesmo terminal, sem sudo:\n\n  {value0}\n\nIsso "
                    "remove somente o pacote antigo. Seu PAT e as configurações "
                    "são preservados.\n3. Execute novamente o instalador:\n\n  "
                    "{value1}\n\n4. Quando a instalação terminar, adicione LG "
                    "ThinQ AirCon Widget à barra novamente."
                ).format(value0=self.remove_widget_command(), value1=self.retry_command())
            )
        self.check_owner()

    def check_owner(self):
        # Query the name owner without activating any service or touching credentials.
        result = run(
            [
                sys.executable,
                "-c",
                "import dbus; b=dbus.SessionBus(); "
                f"print(b.get_name_owner('{SERVICE}') if b.name_has_owner('{SERVICE}') else '')",
            ],
            capture_output=True,
            text=True,
        )
        if not result.stdout.strip():
            return
        owner_pid = run(
            [
                sys.executable,
                "-c",
                "import dbus; b=dbus.SessionBus(); "
                "o=b.get_object('org.freedesktop.DBus','/org/freedesktop/DBus'); "
                f"print(o.GetConnectionUnixProcessID('{SERVICE}', "
                "dbus_interface='org.freedesktop.DBus'))",
            ],
            capture_output=True,
            text=True,
        ).stdout.strip()
        unit_pid = run(
            ["systemctl", "--user", "show", UNIT, "--property=MainPID", "--value"],
            capture_output=True,
            text=True,
        ).stdout.strip()
        if not self.unit.exists() or MARKER not in self.unit.read_text() or owner_pid != unit_pid:
            raise ValueError(
                gettext(
                    "Backend anterior está em execução. Encerre o terminal dele "
                    "ou a unidade lgthinq.service antes de instalar; nenhum "
                    "processo foi encerrado.\nSe você iniciou Python/serve em um "
                    "terminal, volte a esse terminal e pressione Ctrl+C uma vez. "
                    "Não é necessário fechar os outros terminais.\nSe iniciou "
                    "pelo systemd, execute: systemctl --user disable --now "
                    "lgthinq.service\nDepois, tente novamente:\n\n  {value0}"
                ).format(value0=self.retry_command())
            )

    def write_registration(self):
        python = self.current / "venv/bin/python"
        config = self.config / "lgthinq-kde/config.json"
        args = (
            f"{quoted(python)} -m lgthinq_daemon --config "
            f"{quoted(self.config / 'lgthinq-kde/config.json')} serve-local"
        )
        self.unit.parent.mkdir(parents=True, exist_ok=True)
        self.unit.write_text(
            f"{MARKER}\n[Unit]\nDescription=LG ThinQ AirCon Widget\n"
            "PartOf=graphical-session.target\nStartLimitIntervalSec=60\nStartLimitBurst=3\n"
            f"[Service]\nType=dbus\nBusName={SERVICE}\nExecStart={args}\n"
            "Restart=on-failure\nRestartSec=5\nUMask=0077\nNoNewPrivileges=true\n"
        )
        self.activation.parent.mkdir(parents=True, exist_ok=True)
        # systemd performs startup; Exec is a valid fallback for other session buses.
        self.activation.write_text(
            f"{MARKER}\n[D-BUS Service]\nName={SERVICE}\n"
            f"Exec={quoted(python, systemd=False)} -m lgthinq_daemon "
            f"--config {quoted(config, systemd=False)} serve-local\nSystemdService={UNIT}\n"
        )

    def package(self, archive, *, installed):
        run(
            [
                "kpackagetool6",
                "--type",
                "Plasma/Applet",
                "--packageroot",
                str(self.packages),
                "--upgrade" if installed else "--install",
                str(archive),
            ]
        )

    def install(self, payload):
        print(
            gettext("[1/4] Verificando se este computador está pronto para instalar…"), flush=True
        )
        self.preflight()
        # The checkout entry point must obey the same policy as the zipapp.
        # Validate all selected inputs before pip or any installation mutation.
        selected = {
            name: source_file(payload, name)
            for name in [
                "pyproject.toml",
                "BACKEND.md",
                "MANIFEST.in",
                "LICENSE",
                "LICENSE-DOCS",
                "NOTICE",
                "README.md",
                *[f"src/lgthinq_daemon/{n}" for n in BACKEND],
                *backend_catalogs(),
            ]
        }
        selected.update(
            {f"plasmoid/{name}": path for name, path in sources(payload, "plasmoid").items()}
        )
        if self.root.exists() and not self.receipt.exists():
            raise ValueError(
                gettext("Diretório local sem recibo gerenciado; revise antes de instalar")
            )
        previous = self.current.resolve() if self.current.exists() else None
        backup = {
            p: p.read_bytes() if p.exists() else None
            for p in [self.unit, self.activation, self.receipt]
        }
        release = self.root / "releases" / str(time.time_ns())
        release.mkdir(parents=True)
        committed = False
        package_changed = False
        try:
            source = release / "source"
            source.mkdir()
            for name, path in selected.items():
                destination = source / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, destination)
            print(
                gettext("[2/4] Preparando o componente local e baixando dependências Python…"),
                flush=True,
            )
            print(
                gettext("Isso pode levar alguns minutos. Aguarde sem fechar este terminal."),
                flush=True,
            )
            run([sys.executable, "-m", "venv", "--system-site-packages", str(release / "venv")])
            python = release / "venv/bin/python"
            run(
                [
                    str(python),
                    "-m",
                    "pip",
                    "install",
                    "--disable-pip-version-check",
                    "--no-input",
                    f"{source}[thinq]",
                ]
            )
            run(
                [
                    str(python),
                    "-c",
                    "import dbus, gi, keyring, aiohttp, thinqconnect, lgthinq_daemon.local",
                ]
            )
            run([str(python), "-m", "pip", "check"])
            archive = release / "lgthinq.plasmoid"
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as package:
                for member, path in sources(source, "plasmoid").items():
                    package.write(path, member)
            validate_archive(archive, "plasmoid")
            # No host services or widget files are changed before runtime validation.
            print(
                gettext("[3/4] Instalando o widget e configurando a inicialização automática…"),
                flush=True,
            )
            self.package(archive, installed=self.widget.exists())
            package_changed = True
            if previous:
                run(["systemctl", "--user", "stop", UNIT])
            temporary = self.root / ".current-new"
            temporary.symlink_to(release.relative_to(self.root))
            temporary.replace(self.current)
            self.write_registration()
            run(["systemd-analyze", "--user", "verify", str(self.unit)])
            run(["systemctl", "--user", "daemon-reload"])
            reload_activation()
            self.receipt.write_text(json.dumps({"format": 1, "release": release.name}) + "\n")
            committed = True
        finally:
            if not committed:
                for path, content in backup.items():
                    if content is None:
                        path.unlink(missing_ok=True)
                    else:
                        path.write_bytes(content)
                if previous:
                    link = self.root / ".rollback"
                    link.symlink_to(previous)
                    link.replace(self.current)
                else:
                    self.current.unlink(missing_ok=True)
                if package_changed:
                    if previous:
                        self.package(previous / "lgthinq.plasmoid", installed=True)
                    else:
                        run(
                            [
                                "kpackagetool6",
                                "--type",
                                "Plasma/Applet",
                                "--packageroot",
                                str(self.packages),
                                "--remove",
                                "org.lgthinq.aircon",
                            ]
                        )
                shutil.rmtree(release)
                run(["systemctl", "--user", "daemon-reload"])
                reload_activation()
                if not previous:
                    shutil.rmtree(self.root)
        print(gettext("[4/4] Instalação concluída!"))
        print(
            gettext(
                "Clique com o botão direito na barra do KDE → Adicionar widgets "
                "→ procure LG ThinQ AirCon Widget."
            )
        )
        print(gettext("Adicione-o à barra; depois abra Configurações → Conexão e credenciais."))
        print(
            gettext(
                "Informe PAT/país e clique em Salvar e conectar. Nenhum PAT foi "
                "lido pelo instalador."
            )
        )
        if previous:
            print(
                gettext(
                    "Atualização concluída. Reabra a instância do widget para "
                    "carregar o QML atualizado."
                )
            )

    def remove(self):
        self.preflight(removing=True)
        if not self.receipt.exists():
            raise ValueError(gettext("Nenhuma instalação local gerenciada encontrada"))
        self.activation.unlink(missing_ok=True)
        run(["systemctl", "--user", "stop", UNIT])
        if self.widget.exists():
            run(
                [
                    "kpackagetool6",
                    "--type",
                    "Plasma/Applet",
                    "--packageroot",
                    str(self.packages),
                    "--remove",
                    "org.lgthinq.aircon",
                ]
            )
        self.unit.unlink(missing_ok=True)
        run(["systemctl", "--user", "daemon-reload"])
        reload_activation()
        shutil.rmtree(self.root)
        print(
            gettext(
                "Removido. Remova a instância do painel. Configuração e "
                "credencial foram preservadas."
            )
        )
        print(
            gettext(
                "Para apagar a configuração: gerencie "
                "~/.config/lgthinq-kde/config.json (ou XDG_CONFIG_HOME)."
            )
        )
        print(
            gettext(
                "No cofre, remova lgthinq-kde-widget/default; revogue o PAT no "
                "portal LG se necessário."
            )
        )


def main():
    parser = argparse.ArgumentParser(
        description=gettext(
            "Instala LG ThinQ AirCon Widget no seu usuário KDE: widget e conexão local automática."
        )
    )
    parser.add_argument(
        "action",
        choices=["install", "update", "remove", "check"],
        nargs="?",
        default="install",
        help=gettext(
            "install: instalar; update: atualizar; remove: desinstalar; check: só verificar"
        ),
    )
    args = parser.parse_args()
    try:
        installer = Installer()
        if args.action == "remove":
            installer.remove()
        elif args.action == "check":
            installer.preflight()
            print(
                gettext(
                    "Pré-requisitos locais verificados; cofre/credencial serão "
                    "validados na configuração gráfica."
                )
            )
            print(
                gettext("Para instalar, execute:\n\n  {value0}").format(
                    value0=installer.retry_command()
                )
            )
        else:
            # A zipapp includes its payload; a source checkout is also supported.
            if zipfile.is_zipfile(sys.argv[0]):
                with tempfile.TemporaryDirectory(prefix="lgthinq-payload-") as directory:
                    with zipfile.ZipFile(sys.argv[0]) as bundle:
                        for name in bundle.namelist():
                            if name.startswith("payload/"):
                                bundle.extract(name, directory)
                    installer.install(Path(directory) / "payload")
            else:
                installer.install(Path(__file__).resolve().parents[1])
        return 0
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        # No SDK/vault is invoked by this installer; diagnostics contain only install paths.
        print(gettext("\nNão foi possível concluir esta operação.\n"), file=sys.stderr)
        if isinstance(exc, ValueError):
            print(str(exc), file=sys.stderr)
        elif isinstance(exc, subprocess.CalledProcessError):
            print(
                gettext("Um dos passos retornou erro. A última saída do programa aparece acima."),
                file=sys.stderr,
            )
            print(
                gettext("Passo que falhou: {value0}").format(value0=shlex.join(map(str, exc.cmd))),
                file=sys.stderr,
            )
            print(
                gettext(
                    "Se o erro ocorreu no download, confira a internet e execute "
                    "novamente o instalador."
                ),
                file=sys.stderr,
            )
        else:
            print(
                gettext(
                    "Não foi possível acessar um arquivo ou executar um programa: {value0}"
                ).format(value0=exc),
                file=sys.stderr,
            )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
