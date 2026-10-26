# Compatibilidade Plasma, Qt e sistema

Revisão de fontes oficiais por tag em 2026-10-23 e API instalada no host.
**Piso de API não equivale a suporte validado em runtime.** Metadata declara 6.4
em vez de 6.0 porque o código depende de SignalWatcher, sem fallback.

| Plasma Workspace | Qt de referência | Recursos QML / dependências | Verificação | Limitações |
|---|---|---|---|---|
| 6.0.0 | mínimo upstream 6.6 | Caminho components/dbus ausente na tag consultada | Não atende ao requisito deste widget | Sem runtime nesta fase; não suportado pelo requisito declarado |
| 6.3.0 / 6.3.5 | mínimo upstream 6.7 | SessionBus e DBusServiceWatcher presentes; SignalWatcher não incluído no target | CMake da tag e ausência do header confirmados | Sem fallback de sinais; incompatível com o código atual |
| 6.4.0 | mínimo upstream 6.8 | SignalWatcher, SessionBus.asyncCall, pending reply e DBusServiceWatcher presentes | Registro QML, propriedades e implementação do handler conferidos | Candidato pelo piso da API; runtime completo ainda não testado |
| 6.5–6.7 | Conforme distribuição | Mesma API exigida | Não exercitado nem verificado tag a tag | Não declarar certificação por interpolação |
| 6.8.0 instalado | Qt 6.12.0 | D-Bus 1.0, QtQuick/Controls/Layouts/Window, Kirigami 6.31, libplasma 6.8 | qmltypes instalado conferido; suíte sintética no host | Simulação não aprova todos os temas, hardware, cofre ou sessão real |

## Evidência de API

- [Target D-Bus 6.3.5](https://github.com/KDE/plasma-workspace/blob/v6.3.5/components/dbus/CMakeLists.txt): sem dbussignalwatcher.
- [Target 6.4.0](https://github.com/KDE/plasma-workspace/blob/v6.4.0/components/dbus/CMakeLists.txt): compila o watcher.
- [Registro SignalWatcher 6.4.0](https://github.com/KDE/plasma-workspace/blob/v6.4.0/components/dbus/dbussignalwatcher.h): QML_NAMED_ELEMENT e propriedades enabled, busType, service, path, iface.
- [Implementação 6.4.0](https://github.com/KDE/plasma-workspace/blob/v6.4.0/components/dbus/dbussignalwatcher.cpp): despacho para prefixo dbus + nome do sinal; corresponde aos handlers do projeto.
- [SessionBus e asyncCall](https://github.com/KDE/plasma-workspace/blob/v6.4.0/components/dbus/dbusconnection.h), [pending reply](https://github.com/KDE/plasma-workspace/blob/v6.4.0/components/dbus/dbuspendingreply.h): finished, value, isError usados pelo projeto.
- [Requisitos Qt 6.4.0](https://github.com/KDE/plasma-workspace/blob/v6.4.0/CMakeLists.txt): QT_MIN_VERSION 6.8.0.
- [Requisitos Qt 6.8.0](https://github.com/KDE/plasma-workspace/blob/v6.8.0/CMakeLists.txt): QT_MIN_VERSION 6.11.0; o host usa 6.12.

No host, dbusplugin.qmltypes exporta SignalWatcher 1.0 e DBusServiceWatcher 1.0.
Foram comparadas também as fontes 6.8.0 das chamadas e sinais. Não foi compilado
ou executado Plasma 6.4.0; Qt mínimo upstream não é uma matriz testada pelo projeto.
`pragma ComponentBehavior: Bound`, QtQuick Controls, ScrollView e Canvas precisam
ser exercitados junto com menus/configuração/diálogo nas versões candidatas.

## Requisitos operacionais

- Linux, Python 3.11+ com venv/pip; resolução real desta fase é Python 3.14.8.
- dbus-python e PyGObject/GLib compatíveis com o Python que cria o venv.
- Sessão D-Bus e systemd de usuário; kpackagetool6, systemctl, systemd-analyze e
  dbus-send para o instalador integrado. Não instalar serviços de sistema.
- KWallet/Secret Service seguro/desbloqueado e internet/PAT para uso real, fora de CI.
- O instalador procura qmltypes em `/usr/lib/qt6` ou `/usr/lib64/qt6`; layouts de
  outras distribuições exigem validação/adaptação. Metadata sozinha não verifica isso.

O ID público é org.lgthinq.aircon; Python, pyproject e metadata de produção usam
1.0.0rc1. Autoria pública é coletiva e os recursos próprios usam GPL-3.0-or-later.
D-Bus/Plasma adotam namespace neutro; instalações antigas exigem reinstalação.
URLs pessoais foram omitidas dos metadados por decisão do mantenedor.

## Aceitação preparada

A [matriz operacional](OPERATIONAL_ACCEPTANCE.md) fornece pré-requisitos, comandos,
critérios, recuperação e registro para cada ensaio. Nesta execução o host continua
Plasma 6.8/Qt 6.12, com validação sintética; não houve novo login, cofre real,
certificação de Plasma 6.4 ou comando físico. O gate homelab agora impede execução
do instalador; isso não altera compatibilidade técnica nem regulariza a imagem.

O viewer isolado de produção também passou com backend sintético, painel/menu,
configuração, edição de temperatura e perda/recuperação do serviço. Avisos do
containment de desktop/Kirigami e serviços ausentes no bus privado continuam
registrados; não constituem certificação de composição no plasmashell instalado.
