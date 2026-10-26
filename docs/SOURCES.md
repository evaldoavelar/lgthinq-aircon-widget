# Fontes técnicas e proveniência

Esta página conserva referências históricas de 2026-10-22. Estado instalado atual,
limites de compatibilidade e licenças foram reavaliados na revisão de dependências; consulte
[COMPATIBILITY](COMPATIBILITY.md), [LICENSING](LICENSING.md) e
[DEPENDENCIES](DEPENDENCIES.md). Links de documentação são referências, não
declarações de incorporação ou autorização para relicenciar seu conteúdo.

Data de preparação deste conjunto: 2026-10-22. Verificar as páginas novamente na fase em que forem utilizadas; URLs e implementações podem mudar.

## KDE Plasma 6 / QML

- Guia oficial para iniciar um widget: https://develop.kde.org/docs/plasma/widget/setup/
- Porting Plasmoids para KF6: https://develop.kde.org/docs/plasma/widget/porting_kf6/
- Propriedades de metadata: https://develop.kde.org/docs/plasma/widget/properties/
- Exemplo de uso de `org.kde.plasma.workspace.dbus` e `SessionBus.asyncCall`: https://discuss.kde.org/t/using-dbus-in-plasmoid/40321
- Changelog Plasma que menciona `SignalWatcher` nos componentes D-Bus: https://kde.org/announcements/changelogs/plasma/6/6.3.5-6.3.90/

## Qt for Python / D-Bus (referência histórica da PoC inicial)

- PySide6 `ClassInfo`, que mapeia para `Q_CLASSINFO`: https://doc.qt.io/qtforpython-6/PySide6/QtCore/ClassInfo.html
- Qt for Python, exemplo de listagem D-Bus: https://doc.qt.io/qtforpython-6/examples/example_dbus_listnames.html
- Qt for Python, exemplo D-Bus Ping/Pong: https://doc.qt.io/qtforpython-6/examples/example_dbus_pingpong.html
- Qt for Python D-Bus API: https://doc.qt.io/qtforpython-6/PySide6/QtDBus/index.html

## LG ThinQ Connect

- Portal de PAT: https://connect-pat.lgthinq.com/
- SDK: https://github.com/thinq-connect/pythinqconnect
- Integração do Home Assistant: https://www.home-assistant.io/integrations/lg_thinq/

## Fontes efetivamente verificadas nesta missão (2026-10-22)

- [KDE DBusConnection](https://github.com/KDE/plasma-workspace/blob/master/components/dbus/dbusconnection.h)
- [KDE SignalWatcher](https://github.com/KDE/plasma-workspace/blob/master/components/dbus/dbussignalwatcher.h)
- SDK LG: README, setup.py, thinq_api.py, devices/air_conditioner.py e
  devices/connect_device.py no repositório oficial já listado acima. Distribuição
  `thinqconnect`, setup upstream 1.0.14; dependência fixada, instalação não comprovada.
- Inspeção local de dbusplugin.qmltypes e kde-qmlmodule.version (6.8.0) validou a
  superfície QML instalada. A fonte `master/main` é mutável; não equivale a pacote
  instalado. Conferir novamente antes de atualizar dependências.

O fórum KDE listado inicialmente é contexto, não foi usado como prova primária.
Nenhuma especificação de aparelho é inferida da existência de um método SDK.

Configuração Plasma validada conforme [guia oficial KDE](https://develop.kde.org/docs/plasma/widget/configuration/) e tipos QML instalados.

Ícone empacotado: [resolução no modelo do Widget Explorer KDE](https://github.com/KDE/plasma-workspace/blob/master/components/shellprivate/plasmaappletitemmodel.cpp). Caminho /images/lgthinq.svg validado também no KPackage instalado do host.

## Fontes reconsultadas na investigação de conformidade (2026-10-23)

- [ThinQ Connect LICENSE, tag 1.0.14](https://github.com/thinq-connect/pythinqconnect/blob/1.0.14/LICENSE): declaração upstream, confrontada com o texto instalado.
- [AWS SDK LICENSE](https://github.com/aws/aws-iot-device-sdk-python-v2/blob/v1.31.0/documents/LICENSE) e [NOTICE](https://github.com/aws/aws-iot-device-sdk-python-v2/blob/v1.31.0/documents/NOTICE): textos fixados, hashes reconfirmados.
- [AWS CRT gitmodules v0.36.1](https://github.com/awslabs/aws-crt-python/blob/v0.36.1/.gitmodules) e [build README](https://github.com/awslabs/aws-crt-python/blob/v0.36.1/README.md): gitlinks e possibilidade de incorporação estática, não atestado do wheel.
- [cryptography 50.0.2 Cargo.lock](https://github.com/pyca/cryptography/blob/50.0.2/Cargo.lock): candidatos Rust; não declara licenças de todas as crates.
- [LG legal](https://www.lg.com/global/legal/) e [KDE clipart](https://kde.org/stuff/clipart/): limites sobre materiais/marcas, sem autorização inferida para recursos locais.
- [KDE i18n](https://develop.kde.org/docs/plasma/widget/translations-i18n/): mecanismo Ki18n usado na marcação inicial, sem copiar traduções.
- [Redistribuição Debian](https://www.debian.org/doc/manuals/debian-faq/redistributing.en.html): cumprir termos por componente, não apenas listar pacotes.

Consultas exatas pelo nome/SVG e por um traço do Canvas não localizaram origem
pública verificável. Isso é resultado de busca limitada, não prova de ausência de
cópia. O endpoint LG recusou aquisição direta com 403, mas sua declaração legal
foi consultada pela ferramenta de navegação; a limitação está registrada externamente.
Textos upstream obtidos e falhas HTTP têm URL/hash/data no relatório externo.
As fontes de componentes nativos estão fixadas por revisão em [NATIVE_COMPONENTS](NATIVE_COMPONENTS.md).

## Investigação e artes propostas após H01–H04 (2026-10-24)

Foram confrontados novamente os seis fontes gráficos/composição com snapshots e
blobs já preservados. Oito versões por hash estão guardadas externamente; nenhuma
comprova criador/permissão. A referência histórica KDE Connect no ADR-0009 foi
registrada separadamente de origem de código/arquivo, sem inferir cópia/licença.
A UI importa QtQuick/Controls/Layouts e KDE Kirigami/Plasma do host; ícones de tema
são lookup em runtime, sem biblioteca de desenhos incorporada que comprove a origem.

A [receita textual nova](ARTWORK.md) é a fonte técnica das substituições; não usou
screenshot ou paths de terceiro como entrada de desenho. O processo assistido,
reuso funcional e os hashes estão em [graphics-provenance.json](graphics-provenance.json).
Recursos antigos foram vistos para auditoria; não se alega clean room ou liberação.
