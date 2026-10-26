# LG ThinQ AirCon Widget — instalador local para revisão

Distribuição pública autorizada pelo mantenedor em 2026-10-26.
Código, exemplos executáveis, testes, configuração, catálogos e recursos SVG/QML
próprios: GPL-3.0-or-later. Prosa própria: CC BY 4.0, com atribuição a
LG ThinQ AirCon Widget contributors. Textos completos em LICENSE e LICENSE-DOCS;
NOTICE delimita o escopo. Direitos e avisos de terceiros permanecem próprios.

## Requisitos

Linux, Plasma Workspace 6.4+ (exercitado somente em 6.8/Qt 6.12), Python 3.11+,
dbus-python, PyGObject/GLib, systemd de usuário, kpackagetool6, pip/venv e cofre
KWallet/Secret Service. O Python precisa ser compatível com as bibliotecas do
sistema. O instalador baixa dependências Python para um runtime do usuário;
é necessário acesso ao índice Python. Não instala ferramentas globais.

## Instalar e atualizar

Em um terminal na pasta que contém o arquivo recebido para revisão, como usuário
normal, sem sudo:

```sh
python3 ./lgthinq-local.pyz install
```

Para atualizar, execute o mesmo comando com o novo arquivo revisado. Não precisa
do checkout. O comando --help mostra as opções. Se houver instalação antiga não
gerenciada, siga o diagnóstico do instalador; não apague arquivos desconhecidos.

Adicione LG ThinQ AirCon Widget ao painel. Abra Configurar → Conexão e credenciais, informe PAT
e país e use Salvar e conectar; selecione o aparelho se houver vários. O PAT fica
no cofre e não deve ser colocado em arquivos ou comandos. Ative Permitir comandos
somente se desejar controle físico. O serviço inicia sob demanda pelo D-Bus.

Sem cofre disponível a gravação falha, sem fallback em arquivo. Verifique a sessão
D-Bus, desbloqueio do cofre e requisitos locais em caso de erro. Não envie PAT,
identificadores privados ou respostas LG ao relatar problemas. Use as issues do repositório do projeto para suporte.

## Remover

Remova as instâncias do painel e, na pasta que contém o instalador, execute:

```sh
python3 ./lgthinq-local.pyz remove
```

Configuração e credenciais são preservadas. Não há Go operacional: cofre real,
novo login e controle físico permanecem sujeitos à aceitação manual. Testes
sintéticos não comprovam compatibilidade com um aparelho específico.

Produto: LG ThinQ AirCon Widget 1.0.0rc1, exclusivo para ar-condicionado em KDE Plasma 6.
Identificadores públicos usam o namespace neutro org.lgthinq.
Catálogos en/pt_BR preparados usam fallback; nenhuma tradução foi aprovada.
