# LG ThinQ AirCon Widget — Plasma 6, pacote local de revisão

Distribuição pública autorizada pelo mantenedor em 2026-10-26.
Código, exemplos executáveis, testes, configuração, catálogos e recursos SVG/QML
próprios: GPL-3.0-or-later. Prosa própria: CC BY 4.0, com atribuição a
LG ThinQ AirCon Widget contributors. Textos completos em LICENSE e LICENSE-DOCS;
NOTICE delimita o escopo. Direitos e avisos de terceiros permanecem próprios.

## Requisitos e backend

Linux e Plasma Workspace 6.4+ como piso de API; runtime exercitado somente em
Plasma 6.8/Qt 6.12. Este .plasmoid não instala o backend Python.
É necessário o instalador local lgthinq-local.pyz da mesma revisão, com Python
3.11+, dbus-python, PyGObject/GLib, systemd de usuário, kpackagetool6, pip/venv e
KWallet/Secret Service. Se recebeu somente o widget, obtenha o instalador revisado
com o mantenedor antes de prosseguir. Fontes e suporte estão no repositório do projeto.

Na pasta que contém o instalador, como usuário normal, sem sudo:

```sh
python3 ./lgthinq-local.pyz install
```

Ele instala backend e widget; repetir com a nova versão atualiza o produto.
Baixa dependências Python em runtime do usuário. Não depende do checkout.
Adicione LG ThinQ AirCon Widget ao painel e abra Configurar → Conexão e credenciais.
Informe PAT/país, use Salvar e conectar e selecione o aparelho, se houver vários.
O PAT segue para o cofre, sem persistir em KConfig. Sem cofre, não há fallback em
arquivo. Permitir comandos habilita controle físico por decisão do usuário.
O backend inicia sob demanda pelo D-Bus, sem terminal aberto ou servidor HTTP.

## Instalação avançada somente do widget

Somente com backend correspondente já instalado, na pasta que contém o .plasmoid:

```sh
kpackagetool6 --type Plasma/Applet --install ./lgthinq.plasmoid
```

Para atualização use --upgrade no lugar de --install. Remova e adicione novamente
a instância do painel para recarregar o QML. Para remover somente o widget, remova
as instâncias e execute:

```sh
kpackagetool6 --type Plasma/Applet --remove org.lgthinq.aircon
```

Para remover o produto integrado use python3 ./lgthinq-local.pyz remove na pasta
do instalador. Configurações e credenciais são preservadas.

Conexão/aparelho são compartilhados na sessão; aparência, unidade e rótulo são por
instância. Capacidades vêm do perfil LG. Windows permanece futuro. Em falhas,
confira requisitos, sessão D-Bus e cofre desbloqueado; relatos devem omitir PAT e
IDs privados. Cofre real, novo login e controle físico aguardam aceitação manual.

Este README é autossuficiente no pacote. Os guias completos do checkout ficam em
docs/INSTALL.md e docs/DEPLOY.md na árvore de fontes, que não acompanha o .plasmoid;
esses caminhos são referências ao checkout, não instruções necessárias ao pacote.

Produto: LG ThinQ AirCon Widget 1.0.0rc1, exclusivo para ar-condicionado em KDE Plasma 6.
Identificadores públicos usam o namespace neutro org.lgthinq.
Catálogos en/pt_BR preparados usam fallback; nenhuma tradução foi aprovada.
