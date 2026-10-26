# Deploy KDE e backend local/remoto

Procedimentos locais de desenvolvimento; nenhuma redistribuição está liberada.
Consulte [DISTRIBUTION](DISTRIBUTION.md) para backend, KDE Store e avisos por artefato.
O pacote `.plasmoid` sozinho não instala o backend Python.

O caminho padrão é a [instalação local integrada](INSTALL.md), com configuração
gráfica e ativação automática. Este guia preserva os procedimentos manuais avançados.
Para a alternativa de servidor central, consulte [Docker/homelab](HOMELAB.md).
Este guia instala o widget e sua ponte no computador KDE. No modo homelab, configure
`--endpoint https://SEU_SERVIDOR configure` e use `api-credential-set`, não o PAT LG.
Depois execute o mesmo `serve` e gere as unidades abaixo. O PAT fica no container.
No modo local alternativo, as instruções credential-set abaixo continuam válidas.

No fluxo integrado, aparência e conexão pertencem ao menu do widget; o PAT é
transitório até o cofre. Os comandos abaixo são a alternativa manual de diagnóstico.

## Configurar conexão uma vez

Execute em terminal privado, na pasta do projeto, quando desejar gravar configurações
locais não secretas:

```sh
PYTHONPATH=src .venv-runtime/bin/python -m lgthinq_daemon --country BR --device-index 0 configure
PYTHONPATH=src .venv-runtime/bin/python -m lgthinq_daemon credential-set
PYTHONPATH=src .venv-runtime/bin/python -m lgthinq_daemon status
PYTHONPATH=src .venv-runtime/bin/python -m lgthinq_daemon serve
```

`configure` cria `$XDG_CONFIG_HOME/lgthinq-kde/config.json` (ou
`~/.config/lgthinq-kde/config.json`). Gera UUID uma única vez e preserva em reexecuções.
Aceita `country`, `client_id`, `account`, `device_index`, `device_id`, `endpoint` opcional e `allow_control` booleano; qualquer campo
extra, inclusive token, é rejeitado. A gravação atômica evita arquivo parcial.
Esse JSON não é um cofre e nunca deve conter credencial. `credential-set` solicita
PAT por entrada oculta e grava exclusivamente no Secret Service/KWallet configurado.

`--config /caminho/config.json` seleciona outro arquivo em qualquer comando. Arquivo
explicitamente solicitado e ausente/inválido causa erro. Argumentos explícitos
prevalecem sobre o JSON; sem JSON, argumentos antigos continuam aceitos. `--device`
explícito substitui índice salvo. O índice depende da ordem da descoberta: confira
`discover` após mudanças na conta. O daemon real inicia somente leitura por padrão. Para liberar controles manualmente,
reinicie com `--allow-control serve`; para salvar a escolha no JSON existente, execute
`--allow-control configure`. `--no-allow-control serve` desabilita escrita nesta execução.

## Gerar artefatos, sem instalar

```sh
python3 scripts/prepare_deploy.py --output dist/local --python "$PWD/.venv-runtime/bin/python" --config "$HOME/.config/lgthinq-kde/config.json"
```

São gerados `dist/local/lgthinq.plasmoid`, `lgthinq.service` (LG real, permissão conforme JSON) e
`lgthinq-simulated.service` (simulação). Não há cópia para HOME, instalação no Plasma,
reload de systemd, habilitação ou inicialização. O arquivo real usa `--config` e
não carrega PAT em variáveis de ambiente. A unidade seleciona explicitamente
`keyring.backends.SecretService.Keyring`; se você usou KWallet, ajuste somente esse
nome de backend no arquivo gerado antes de instalar, usando o mesmo cofre do cadastro. O template inclui caminhos absolutos para
esta cópia do projeto; gere novamente ao mover o repositório/ambiente virtual.
Os dois serviços possuem o mesmo nome D-Bus: execute apenas um por vez.

## Instalação, atualização e remoção do widget

Na raiz do checkout, use a mesma packageroot para consultar e instalar:

```sh
kpackagetool6 --type Plasma/Applet --packageroot "${XDG_DATA_HOME:-$HOME/.local/share}/plasma/plasmoids" --list
kpackagetool6 --type Plasma/Applet --packageroot "${XDG_DATA_HOME:-$HOME/.local/share}/plasma/plasmoids" --install "$PWD/dist/local/lgthinq.plasmoid"
```

Para atualizar, substitua `--install` por `--upgrade`. Para remover, use `--remove
org.lgthinq.aircon` no lugar do argumento de instalação e do caminho do arquivo.
Execute como usuário da sessão KDE, sem sudo. Adicione/remova instâncias do painel
separadamente. O [instalador integrado](INSTALL.md) gerencia também o backend.

`--upgrade` exige instalação prévia. Se retornar `Plugin org.lgthinq.aircon is not
installed`, confira --list e execute --install na mesma pasta. Esse caso foi reproduzido
em ambiente isolado. Adicionar uma instância à barra ocorre depois da instalação;
remover a instância do painel não é o mesmo que desinstalar o pacote.

O pacote do widget e o processo Python têm ciclos de vida separados. Para QML novo,
recarregue a instância após upgrade; para código Python novo, reinicie o processo.
Instalar o widget não inicia o backend nem habilita controle real.

## Backend opcional com systemd

Somente se desejar iniciar permanentemente o backend/ponte com sua sessão, depois de
configurar cofre e conexão e validar `serve` em primeiro plano, instale a unidade
preparada. Execute deliberadamente estes comandos no seu terminal:

```sh
mkdir -p "$HOME/.config/systemd/user"
cp dist/local/lgthinq.service "$HOME/.config/systemd/user/lgthinq.service"
systemctl --user daemon-reload
systemctl --user enable --now lgthinq.service
```

A unidade usa caminhos gerados para esta cópia do projeto. Regenere/recopie se mover
o repositório ou alterar o template. Evite uma segunda instância em primeiro plano.
Para parar e remover **essa unidade, se você a instalou**:

```sh
systemctl --user disable --now lgthinq.service
rm "$HOME/.config/systemd/user/lgthinq.service"
systemctl --user daemon-reload
```

Configuração e item do cofre são preservados; administre credenciais pelo gerenciador
do cofre ao descomissionar. A opção allow_control salva no JSON define a permissão
de escrita no backend. Instalação/remoção real da unidade e desbloqueio do cofre
continuam sujeitos a validação manual no ambiente alvo.

## Diagnóstico e recarga

Execute os cenários sintéticos de [TESTING](TESTING.md) para verificar UI, controles
e recuperação do serviço. Eles não substituem cofre, hardware ou avaliação visual.
Após atualizar QML, remova e recoloque a instância. Se o Plasma mantiver componentes
antigos, a distribuição pode fornecer esta unidade para reiniciar barra e desktop:

```sh
systemctl --user restart plasma-plasmashell.service
```

Verifique a existência da unidade na sua distribuição antes de usá-la. O desktop e
a barra desaparecem brevemente. Reinicie o backend quando seu código Python ou
configuração mudar; recarregar Plasma não instala nem inicia o backend.

Cada abertura do popup solicita Refresh. Durante edição de temperatura, botões e
slider mostram prévia local e enviam a última seleção após debounce. Falha cancela
a prévia, sem repetição automática de escrita. Energia desabilitada pode indicar
perfil sem permissão ou controle não autorizado; no fluxo manual, confira
`--allow-control`. Nunca atribua sucesso a um comando sem estado confirmado.
