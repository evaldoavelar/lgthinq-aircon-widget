# Instalação local integrada — KDE Plasma 6

Na publicação de 2026-10-26, Plasma e D-Bus adotaram o namespace org.lgthinq.
Instalações anteriores precisam remover o pacote antigo antes de reinstalar;
consulte o ID da instalação antiga com `kpackagetool6 --type Plasma/Applet --list`.
Não há migração automática das instâncias do painel. Configuração e cofre foram
preservados; encerre o backend antigo antes de ativar a nova instalação.


Guia de desenvolvimento/revisão local. A redistribuição do instalador depende dos
gates de [licenciamento](LICENSING.md) e [distribuição](DISTRIBUTION.md).
O `.plasmoid` isolado não instala o backend; este guia trata do produto integrado.
Requisitos e limites de versão estão em [COMPATIBILITY](COMPATIBILITY.md).

O modo padrão conecta o próprio computador à nuvem LG. Não exige Docker, servidor
HTTP, certificado local, chave API do projeto ou terminal aberto durante o uso.
Um componente Python local inicia automaticamente quando o widget solicita o D-Bus.
Internet, PAT compatível com a conta/região e cofre da sessão continuam necessários.
Windows será uma implementação futura; este instalador é exclusivo do KDE/Linux.

## 1. Instalar neste computador, onde o projeto já está salvo

Os exemplos assumem o projeto em `$HOME/Documents/lgthinq-aircon-widget`.
Se o checkout estiver em outro diretório, ajuste esse caminho nos comandos.
**Você não precisa copiar o instalador para outra pasta neste caso.**

Abra o Konsole (terminal do KDE) pelo menu de aplicativos. Execute os comandos
abaixo, uma linha de cada vez, pressionando Enter ao fim de cada linha:

```sh
cd "$HOME/Documents/lgthinq-aircon-widget"
python3 scripts/build_local.py
```

O primeiro comando entra na pasta do projeto. O segundo gera o arquivo:

```text
<raiz-do-projeto>/dist/lgthinq-local.pyz
```

`dist` é uma pasta dentro do projeto. `.pyz` é o arquivo único do instalador;
você não precisa descompactá-lo. Nos comandos, `$HOME` significa a pasta pessoal
do usuário atual, independentemente do nome da conta.
Se salvou o projeto em outro lugar, ajuste somente o caminho do comando `cd`.

**Se você já usa o widget antigo, faça a etapa 2 abaixo antes de instalar.**
Se é a primeira instalação nesse computador, continue com:

```sh
python3 "$HOME/Documents/lgthinq-aircon-widget/dist/lgthinq-local.pyz" install
```

Esse comando usa o caminho completo; não depende de qual pasta o terminal está
mostrando. Não coloque `sudo` antes dele. Execute com seu usuário normal, dentro
da sessão gráfica do KDE (com a barra e a área de trabalho abertas).

Durante a instalação aparecerão quatro etapas: verificação do computador,
preparação/download de dependências, instalação do widget e conclusão. O download
pode levar alguns minutos. Aguarde a mensagem **Instalação concluída!** antes de
fechar o terminal. Não será solicitado PAT nessa etapa.
Depois siga **4. Adicionar à barra e configurar** neste guia.

## 2. Se apareceu “Widget anterior encontrado” ou “instalação antiga”

Essa mensagem significa que você já instalou o pacote manual anterior. O instalador
parou para preservar a instalação existente. Não é um erro no PAT.

**Primeiro, remova a instância antiga da barra:** clique com o botão direito na barra,
entre no modo de edição e use a ação **Remover** do widget LG ThinQ AirCon Widget. Saia do modo de
edição. Isso retira o item da barra; o próximo comando remove o pacote antigo instalado.

No Konsole, copie o bloco abaixo e pressione Enter:

```sh
kpackagetool6 --type Plasma/Applet \
  --packageroot "${XDG_DATA_HOME:-$HOME/.local/share}/plasma/plasmoids" \
  --remove org.lgthinq.aircon
```

As barras `\` no fim das duas primeiras linhas fazem parte do comando: elas indicam
que a linha continua. Copie as três linhas juntas. O comando pode ser executado de
qualquer pasta e sem sudo. Ele remove **somente o pacote do widget**; PAT no cofre e
configurações da conexão são preservados. Se informar que o pacote não está instalado,
essa parte da remoção já está concluída e você pode continuar.

Se você mantinha o Python rodando em outro terminal, volte ao terminal que mostra o
serviço e pressione **Ctrl+C uma vez** para encerrá-lo. Não é necessário fechar os
outros terminais. Se nunca iniciou um serviço manual ou pelo systemd, pule o parágrafo
seguinte.

**Somente se o instalador apontar `lgthinq.service` antigo**, execute:

```sh
systemctl --user disable --now lgthinq.service
rm -- "${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user/lgthinq.service"
systemctl --user daemon-reload
```

Esses comandos param o serviço antigo, removem seu arquivo de inicialização e fazem
o KDE reler a lista de serviços. Não removem PAT/configuração. Se o arquivo não existir,
o `rm` informa isso; não use um comando mais amplo para tentar apagar outras pastas.
O instalador também imprime esses comandos quando identifica essa situação.

Agora gere novamente o instalador para incluir a versão mais recente e instale:

```sh
cd "$HOME/Documents/lgthinq-aircon-widget"
python3 scripts/build_local.py
python3 "$HOME/Documents/lgthinq-aircon-widget/dist/lgthinq-local.pyz" install
```

Aguarde **Instalação concluída!** e adicione o widget novamente pela etapa 4.
Se surgir outro bloqueio, siga a orientação específica mostrada no terminal; não
apague a configuração nem o PAT para resolver um erro de instalação.

## 3. Instalar em outro computador com KDE

**Procedimento futuro, condicionado à liberação de redistribuição.** Não transfira
o artefato enquanto os direitos e avisos necessários estiverem pendentes.

Pule esta etapa se você vai usar o mesmo computador onde gerou o arquivo.
Não há download público deste `.pyz` publicado como release nesta entrega.

**Origem:** no computador que contém o projeto, gere o arquivo pela etapa 1.
Abra o gerenciador de arquivos Dolphin e entre nesta pasta:

```text
<raiz-do-projeto>/dist/
```

Copie o arquivo **`lgthinq-local.pyz`** dessa pasta para um pendrive ou transfira-o
pelo meio que você costuma usar. Não precisa copiar o repositório, a pasta `src`,
a pasta `plasmoid` ou o ambiente Python.

**Destino:** no outro computador KDE, abra o Konsole e crie uma pasta para guardar
o instalador:

```sh
mkdir -p "$HOME/Documents/LGThinQ"
```

No Dolphin desse computador, abra sua pasta pessoal e entre em **Documents → LGThinQ**.
Cole ali o arquivo trazido pelo pendrive/transferência. O resultado será:

```text
/CAMINHO/ABSOLUTO/Documents/LGThinQ/lgthinq-local.pyz
```

`SEU_USUARIO` é apenas uma indicação do nome da conta nesse outro computador;
não crie uma pasta com esse nome. A pasta `Documents` acima é criada literalmente
pelo comando, mesmo se sua distribuição também tiver uma pasta chamada `Documentos`.

No Konsole do computador de destino, execute:

```sh
python3 "$HOME/Documents/LGThinQ/lgthinq-local.pyz" install
```

Não precisa entrar na pasta com `cd`, descompactar o arquivo ou usar sudo. Se houver
widget antigo também nesse computador, siga os passos de remoção da etapa 2 e repita
o comando de instalação acima, que usa o arquivo copiado para `Documents/LGThinQ`.
Aguarde **Instalação concluída!** e continue na etapa 4.

## O que o computador precisa ter

É necessário Linux com KDE Plasma compatível, Python 3.11+ e internet para baixar
as dependências e depois acessar a LG. O instalador verifica os componentes do
sistema e para com uma explicação se algo estiver faltando; ele não instala pacotes
de sistema automaticamente. Você não precisa iniciar servidor ou deixar terminal
aberto para usar o widget depois de instalado.

Detalhes técnicos dos pré-requisitos, úteis ao pedir suporte: Python com venv/pip,
dbus-python e PyGObject/GLib, Plasma com `org.kde.plasma.workspace.dbus` e SignalWatcher,
`kpackagetool6`, sessão systemd de usuário, `systemd-analyze` e `dbus-send`.
O caminho QML é detectado em `/usr/lib/qt6` ou `/usr/lib64/qt6`; outras distribuições
podem precisar de adaptação. Esta entrega não declara suporte a todo Plasma 6/Linux.

O cofre KWallet/Secret Service guarda o PAT com proteção do sistema. Se aparecer uma
janela de desbloqueio, siga a orientação do cofre do seu computador. Sem cofre
funcional a configuração da conexão mostra erro; não salva PAT em arquivo comum.

## 4. Adicionar à barra e configurar

1. Clique com o botão direito na barra do KDE. Se necessário, entre no modo de edição.
   Escolha **Adicionar widgets**, procure **LG ThinQ AirCon Widget** e arraste-o para a barra.
   Se a lista já estava aberta durante a instalação, feche e abra a lista novamente.
2. Clique com o botão direito no widget LG ThinQ AirCon Widget e abra **Configurar LG ThinQ AirCon Widget**
   (o nome pode aparecer apenas como **Configurações**). Entre em **Conexão e credenciais**.
3. Informe o país da conta (inicialmente BR) e o PAT em campo oculto. Obtenha o PAT
   no [portal oficial LG](https://connect-pat.lgthinq.com/) pelo navegador.
4. Marque **Permitir comandos ao aparelho** se quiser usar os controles.
5. Clique **Salvar e conectar**, desbloqueando o cofre se solicitado.
6. Um único ar-condicionado é selecionado automaticamente. Se houver vários,
   escolha o desejado e clique **Salvar e conectar** novamente.

Esta aba tem seu próprio botão de salvar; não depende do botão Aplicar do diálogo.
O PAT não é exibido novamente e não é salvo na configuração comum do Plasma.
Campo vazio mantém a credencial existente. Para substituí-la, informe um PAT novo
e salve. UUID é gerado automaticamente; seleção usa ID estável do aparelho.
Sem cofre funcional, a conexão apresenta erro e não cria arquivo de credenciais.
Não é preciso exportar variável de keyring no fluxo integrado: o componente
seleciona Secret Service ou KWallet seguro disponível. Overrides explícitos de
keyring continuam sujeitos à validação dos backends permitidos.

O componente executa na sessão do usuário, sem porta HTTP. Nas próximas sessões,
o widget solicita sua inicialização automaticamente. Falhas de processo têm
reinício limitado pelo systemd e novas solicitações de ativação limitadas no widget.
Revogação do PAT exige substituição nas configurações; falhas de rede usam backoff.
Rede/cofre não bloqueiam a thread de renderização. Comandos mostram estado
confirmado após nova leitura, respeitando capacidades e limites do perfil LG.

## 5. Atualizar ou desinstalar depois

Se a tela mostrar **Componente local indisponível**, a lista de aparelhos ainda
não foi carregada. Atualize pelo procedimento abaixo e clique **Reconectar**.
O instalador atualizado faz o D-Bus reler o registro de inicialização automática,
além de recarregar as unidades systemd; não é necessário apagar o PAT.
Depois, use **Salvar e conectar** para cadastrar a conexão ou **Buscar aparelhos**
se a credencial já estiver no cofre. Selecione o aparelho após a busca terminar.

Escolha **somente uma** das operações abaixo. Se usa o arquivo no computador do
projeto, para atualizar execute:

```sh
cd "$HOME/Documents/lgthinq-aircon-widget"
python3 scripts/build_local.py
python3 "$HOME/Documents/lgthinq-aircon-widget/dist/lgthinq-local.pyz" update
```

Se usa o instalador copiado para outro computador, substitua o arquivo em
`Documents/LGThinQ` pela nova versão trazida do computador de origem. Depois execute:

```sh
python3 "$HOME/Documents/LGThinQ/lgthinq-local.pyz" update
```

**Para desinstalar o produto integrado**, no computador do projeto execute:

```sh
python3 "$HOME/Documents/lgthinq-aircon-widget/dist/lgthinq-local.pyz" remove
```

Ou, se usa a cópia na pasta `Documents/LGThinQ`, execute:

```sh
python3 "$HOME/Documents/LGThinQ/lgthinq-local.pyz" remove
```

Use o mesmo usuário da instalação. Não mude os diretórios XDG entre instalar,
atualizar e remover; normalmente você não precisa configurar essas variáveis.
 Atualização prepara e valida um novo runtime
antes de substituir o atual; falhas na ativação do pacote/registro tentam restaurar
a instalação anterior. Releases anteriores ficam preservadas no diretório local.
Depois de atualizar QML, remova/recoloque a instância do painel. Se o Plasma mantiver
componentes antigos, siga a [recarga do Plasma em DEPLOY](DEPLOY.md); o instalador não o faz.

Remoção encerra o componente gerenciado e remove pacote e registro de ativação.
Remova também a instância do painel. Configuração e credencial são preservadas.
Para apagar credenciais, gerencie `lgthinq-kde-widget` e o alias usado (normalmente
`default`) no cofre. Remova a configuração não secreta pelo gerenciador de arquivos
se desejar. Revogue o PAT no portal LG quando necessário.

Arquivos instalados, respeitando XDG:

- `$XDG_DATA_HOME/lgthinq-local/`: runtimes e recibo; padrão `~/.local/share`.
- `$XDG_DATA_HOME/plasma/plasmoids/org.lgthinq.aircon/`: widget.
- `$XDG_DATA_HOME/dbus-1/services/org.lgthinq.LGThinq.service`: ativação.
- `$XDG_CONFIG_HOME/systemd/user/lgthinq-local.service`: processo da sessão.
- `$XDG_CONFIG_HOME/lgthinq-kde/config.json`: opções sem PAT; padrão `~/.config`.

## Se você usava o servidor homelab

O instalador não altera o servidor Docker. A conexão remota salva continua remota.
Para mudar para conexão direta, abra **Conexão e credenciais**, marque a confirmação
**Substituir a conexão homelab por conexão direta neste computador**, informe o PAT
LG e clique **Salvar e conectar**. A chave da API do homelab não substitui o PAT LG.
Para continuar com servidor central, consulte [HOMELAB](HOMELAB.md).

Cofre e JSON existentes são preservados na migração. Um índice antigo é migrado para
ID somente após descoberta válida; índice inválido pede seleção. Credencial antiga
em outro cofre pode exigir recadastro pela interface. CLI e instalação manual são
opções avançadas de diagnóstico em [DEPLOY](DEPLOY.md).

## Verificações de desenvolvimento

```sh
.venv-runtime/bin/python scripts/check.py
.venv-runtime/bin/python -m pytest -q
.venv-runtime/bin/python tests/integration/local_activation.py
.venv-runtime/bin/python scripts/validate_phase0.py --production --panel
```

A integração local usa barramento privado, cofre em memória e clientes sintéticos.
Não consulte credenciais reais nem use comandos físicos em automação. Execução real
do instalador no perfil, desbloqueio do cofre, novo login e controle físico manual
continuam como critérios de aceitação operacional separados dos testes sintéticos.

## Seleção persistida e serviço integrado

`--device ID configure` salva o ID e limpa o índice anterior.
`--device-index N configure` salva o índice e limpa o ID anterior. Informar os dois
simultaneamente é erro, sem escrita. Sem nova seleção, a configuração é preservada.
Na próxima execução, a seleção mais recente é usada. Configurações legadas contendo
ambos ainda preferem o ID estável; a próxima seleção explícita reconcilia o par.
A UI salva ID pela mesma API de configuração e limpa o índice.

`serve-local` usa o JSON salvo e a UI para conexão/seleção: rejeita opções explícitas
`--device`, `--device-index`, `--country`, `--account`, `--client-id`, `--endpoint`,
`--api-token-account`, `--allow-control`, host/porta/TLS e argumentos de comando. Use
`configure` para persistir conexão e seleção, ou a UI integrada. A chave API remota
usa o alias `default` nesse serviço. Os demais comandos mantêm seus overrides.
`--no-allow-control serve-local` impõe somente leitura durante toda a sessão, também
no modo remoto e após reconfiguração pela UI; não altera o JSON ao iniciar. Uma
habilitação salva ou posterior não remove esse bloqueio: reinicie sem a negação
para voltar à política salva. Sem essa opção, preserva o padrão/configuração atual.
