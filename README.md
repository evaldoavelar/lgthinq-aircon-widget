# LG ThinQ AirCon Widget

<img width="555" height="638" alt="image" src="https://github.com/user-attachments/assets/aa41a6fc-e672-442c-852a-9db9e027f15c" />

Controle de **ar-condicionado LG ThinQ para KDE Plasma 6**, pela API oficial
ThinQ Connect. Descobre aparelhos da conta, salva a seleção, lê estado e temperatura,
liga/desliga e oferece temperatura, modo, ventilação e direção do ar **quando o
perfil do aparelho permitir**. Não é um produto oficial da LG ou do KDE.

Código e recursos próprios: **GPL-3.0-or-later**. Documentação própria: **CC BY 4.0**.
Veja [licenciamento](docs/LICENSING.md).

## Requisitos

Linux, Plasma Workspace **6.4+** (piso de API), Python **3.11+**, dbus-python,
PyGObject/GLib, systemd de usuário, kpackagetool6 e **KWallet/Secret Service**.
Internet é necessária para o uso real. A validação sintética usa Plasma 6.8/Qt 6.12;
Plasma 6.4 ainda precisa de ensaio ambiental. Veja [dependências](docs/DEPENDENCIES.md)
e [compatibilidade](docs/COMPATIBILITY.md).

## Instalar e configurar

Na raiz do checkout revisado, como usuário normal da sessão KDE:

```sh
python3 scripts/build_local.py
python3 dist/lgthinq-local.pyz check
python3 dist/lgthinq-local.pyz install
```

O instalador cria um ambiente Python do usuário, baixa os extras declarados e
registra ativação D-Bus sob demanda. Adicione **LG ThinQ AirCon Widget** ao painel.
Abra **Configurar → Conexão e credenciais**, informe PAT e país, clique **Salvar e
conectar** e selecione o aparelho. Obtenha o PAT pelo portal oficial indicado nessa
tela; nunca forneça a senha LG ao widget. Campo PAT vazio preserva a credencial
existente. Ela fica exclusivamente no cofre, sem fallback em arquivo. Marque
**Permitir comandos** para habilitar controle real; o padrão é somente leitura.

O [guia de instalação](docs/INSTALL.md) cobre pré-requisitos, migração, ativação,
instalação em outro computador, cofre e recuperação. O `.plasmoid` sozinho requer
backend instalado; veja o [deploy manual](docs/DEPLOY.md).

## Usar

O painel mostra temperatura ambiente quando informada pelo perfil. Abra o popup
para consultar estado e controles disponíveis. **Atualizar** solicita uma consulta
explícita; abrir o popup também a solicita. A edição de temperatura mostra prévia
local e agrupa passos rápidos; o estado só muda após confirmação do backend.
Nenhuma capacidade ausente é simulada. O widget indica somente leitura,
carregamento, desconexão, autenticação e falhas de rede. Há polling com espera
progressiva, sem promessa de atualização instantânea.

## Atualizar, remover e diagnosticar

```sh
python3 dist/lgthinq-local.pyz update
python3 dist/lgthinq-local.pyz remove
```

Antes de remover, retire a instância do painel. Configuração e credencial são
preservadas; a [remoção completa](docs/INSTALL.md#5-atualizar-ou-desinstalar-depois) explica sua administração
separada. O nome público mudou; IDs, configuração e cofre mantêm os nomes antigos
por compatibilidade, conforme [arquitetura](docs/ARCHITECTURE.md).

Para diagnóstico, comece por `check` e pelo [guia de instalação](docs/INSTALL.md).
Relate versão, etapa e categoria de erro; não compartilhe tokens, IDs de aparelhos,
respostas privadas ou logs sem sanitização.

## Testar sem credenciais

Prepare o ambiente conforme [TESTING](docs/TESTING.md) e execute:

```sh
.venv-runtime/bin/python -m lgthinq_daemon --simulate serve
```

Em outro terminal da mesma sessão, na raiz do checkout:

```sh
plasmoidviewer -a "$PWD/plasmoid"
```

Feche o viewer e encerre o backend com Ctrl+C. São dados sintéticos.

## Limitações e contribuição

Não houve login LG nem comandos físicos na preparação desta candidata. Cofre real,
novo login da sessão, aparelhos e matriz de temas/versões precisam de aceitação
ambiental; simulação não certifica um modelo LG. Inglês e pt_BR têm catálogos de
trabalho preparados, **sem traduções revisadas**: o fallback mantém o texto-fonte
atual, misto. Veja [internacionalização](docs/I18N.md).

- [Contribuir](CONTRIBUTING.md), [testar](docs/TESTING.md) e [manifesto](MANIFEST.md).
- [Arquitetura](docs/ARCHITECTURE.md), [D-Bus](docs/DBUS_CONTRACT.md) e [segurança](docs/SECURITY.md).
- [Artes/proveniência](docs/ARTWORK.md), [direitos](docs/RIGHTS_INVENTORY.md) e [pacotes](docs/DISTRIBUTION.md).
- [Roadmap](docs/ROADMAP.md); [homelab](docs/HOMELAB.md) é avançado e está suspenso.
  O gate da [imagem Docker histórica](docs/DOCKER_COMPLIANCE.md) permanece fechado.

Use as issues e pull requests deste repositório para problemas e contribuições.
Não envie segredos em relatos.
