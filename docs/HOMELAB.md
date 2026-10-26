# Backend central no homelab

Referências de imagem usam `localhost/lgthinq` como identificador local
anonimizado; não indicam um registry público disponível.

**Distribuição suspensa na revisão de dependências.** A imagem anteriormente publicada ainda tem
pendências legais e de proveniência. Os procedimentos abaixo são documentação
técnica/histórica, não uma recomendação de novo deploy ou redistribuição.
Não executar publicação, nova tag ou substituição do digest nesta etapa.
Consulte o [plano de regularização](DOCKER_COMPLIANCE.md).
O instalador standalone agora falha antes de qualquer prompt, leitura de segredo,
pull ou deploy; apenas `--help` está disponível. Os exemplos de provisionamento
abaixo descrevem o motor preservado, sem caminho de execução autorizado.

Os arquivos locais de agentes/contexto permanecem no checkout privado e serão
excluídos do futuro snapshot público. Não entram nos pacotes do produto; avisos
ai-memory dependem de redistribuição efetiva desses materiais. A presença local
não altera o gate Docker ou aprova seus componentes de terceiros. A autorização
histórica descrita no ADR-0007 foi superada pela suspensão atual.

A topologia preparada é:

```text
LG Connect ← backend Python no homelab ← HTTPS /v1 ← clientes
                                                     ├ Linux: ponte Python → D-Bus → Plasmoid
                                                     └ Windows futuro: mesmo JSON, sem D-Bus
```

O PAT LG fica somente no homelab. Os clientes recebem uma chave independente da
API do projeto. A implementação inicial tem uma chave compartilhada; não oferece
ACL por cliente nem administração multiusuário. O modo local continua disponível.
Não foi feito deploy real, exposição de porta, acesso ao cofre ou leitura LG nestes
testes. A imagem Docker foi construída localmente e executada num smoke test isolado. O cliente Windows ainda não foi construído; o contrato HTTP independe de Qt.

## API v1

| Método e caminho | Autenticação | Resultado |
|---|---|---|
| GET /healthz | dispensada | versão 1 e status do processo; não afirma conexão LG |
| GET /v1/snapshot | Bearer | snapshot atual em cache, sem chamada LG |
| POST /v1/refresh | Bearer | leitura LG e snapshot confirmado |
| POST /v1/commands | Bearer | `{ "key": "capability.path", "value": ... }` e snapshot confirmado |

O snapshot tem os mesmos campos de GetSnapshot D-Bus: connection, state,
capabilities, updated_at, error e simulated. Um HTTP 200 pode conter estado de erro
operacional no snapshot; confira ambos. O servidor mantém polling central (15s por
padrão), suspende polling após erro de autenticação e serializa operações. GETs dos
clientes não multiplicam o polling da LG. Não há push nesta versão.

401 significa chave ausente/incorreta; 409 operação em andamento; 429 intervalo
mínimo entre operações; 400 comando inválido/indisponível; 504 timeout. Timeout ou
perda da conexão não comprova que uma escrita foi cancelada no aparelho: consulte
estado antes de repetir. Não há retries automáticos de comandos. Escrita LG real
é bloqueada por padrão; o operador pode habilitá-la explicitamente com
`"allow_control": true` na configuração do servidor. A chave API não altera essa opção.

## Credenciais e transporte

A chave Bearer deve ter ao menos 32 caracteres ASCII sem espaços; gere aleatoriamente
em terminal privado e use o procedimento de entrada oculta da CLI. Nunca reutilize o
PAT LG como chave da API. A chave fica no namespace de cofre `lgthinq-homelab-api`,
separado do namespace LG. Nenhum segredo deve entrar em argumentos, JSON, variável
de ambiente, unidade systemd, URL ou log. HTTPS usa validação normal de certificado
no cliente; não existe opção que desative a verificação TLS.

HTTPS é obrigatório fora de loopback. Um IP pode ser usado desde que o certificado
seja confiável e tenha esse IP no Subject Alternative Name; um nome DNS local com
certificado apropriado costuma facilitar. Uma VPN privada reduz a exposição, mas
não substitui automaticamente HTTPS. Não publique a porta diretamente na internet.
Proxy TLS local pode encaminhar para 127.0.0.1; encaminhe Authorization, limite acesso
no proxy e não registre cabeçalhos. O servidor não confia em X-Forwarded-Proto.

HTTP loopback é permitido apenas para desenvolvimento/teste ou terminação TLS local.
A biblioteca tem override explícito de HTTP inseguro para integração deliberada;
essa opção não foi habilitada na CLI nem nos testes de acesso remoto. O runner recusa
bind externo sem contexto TLS. O cliente rejeita URL com userinfo, query, fragmento
ou prefixo de caminho e não segue redirecionamentos.

Homelab headless pode não ter Secret Service/KWallet desbloqueado. Esse é um requisito
real ainda pendente: não há fallback silencioso em arquivo ou ambiente. Para primeiro
uso escolha uma sessão/cofre suportado e valide seu desbloqueio de forma segura;
não grave PAT em serviço systemd para contornar a falta do cofre.

## Execução preparada

Dependências locais: o servidor LG usa `.[thinq,server]`; cliente remoto pode instalar
`.[remote]` sem SDK LG/AWS. A ponte D-Bus Linux requer bindings do sistema descritos no
guia de instalação. A CLI é integrada separadamente aos módulos abaixo; confira
`python -m lgthinq_daemon --help` para os argumentos finais.

API Python estável nesta entrega:

```python
from lgthinq_daemon.http_api import create_app, run_server
from lgthinq_daemon.remote import RemoteEngine

# token_source: string já em memória ou callable que consulta o cofre.
app = create_app(engine, token_source, timeout=30, min_interval=1, poll_interval=15)
# Primeiro plano, sem instalação; bind externo exige ssl_context configurado.
run_server(engine, token_source, host="127.0.0.1", port=8765)
remote = RemoteEngine("https://homelab.example:8765", token_source)
```

Não execute app e runner sobre o mesmo Engine simultaneamente. `create_app` faz o
polling e fecha engine.client no cleanup. `RemoteEngine.refresh()` lê snapshot em
cache; `request_refresh()` solicita leitura ao servidor; `command(key,value)` valida
capacidade e envia comando. A ponte existente pode usar `serve(remote)`; a sessão
HTTP nasce no loop do worker e é fechada por `remote.client.close()`.

## Evidência e limites

Testes com TestServer aiohttp abrem somente 127.0.0.1 e usam aparelho/chave sintéticos.
Cobrem autenticação, roundtrip remoto, comando simulado confirmado, bloqueio readonly,
409, 429, timeout/recuperação, polling/cleanup e política de URL/TLS. Fontes primárias:
[servidor aiohttp](https://docs.aiohttp.org/en/stable/web_advanced.html) e
[cliente aiohttp](https://docs.aiohttp.org/en/stable/client_reference.html), consultadas
em 2026-10-22. Não há teste de certificado real, LAN/VPN, homelab, cofre headless,
instalação permanente ou cliente Windows. A implantação depende de endereço,
certificado, disponibilidade do cofre e validação de leitura real centralizada.

## Docker preparado (sem deploy executado)

`packaging/docker/Dockerfile` usa Python 3.14 slim, usuário 10001, SDK LG e aiohttp;
não instala D-Bus nem keyring. O contexto permitido em `Dockerfile.dockerignore`
inclui somente código Python, metadados e Dockerfile. Não copie segredos para src.
Build local concluído para `lgthinq-homelab:local`, seguido de smoke test sem rede
externa, sem segredos reais e removido ao encerrar. Na preparação original não houve push nem deploy; a imagem histórica está identificada em DOCKER_COMPLIANCE.md. A tag base e dependências
transitivas não estão presas a hashes; reprodução bit a bit ainda não é garantida.

A variante container adota **explicitamente arquivos de segredo montados em runtime**,
pois o cofre de desktop não existe necessariamente no homelab. Isso é uma decisão
separada, não fallback automático do cofre usado no desktop. Os arquivos permanecem
fora do repositório e da imagem. Compose local faz bind mount e não garante criptografia
em disco no host: permissões de arquivo não equivalem a KWallet/Secret Service. Prefira
integração do homelab com secret manager ou Docker Swarm external secrets se houver
requisitos de armazenamento protegido. A aquisição/gestão dos segredos é responsabilidade
do operador; não insira valores em chat, compose.yaml, `.env`, logs ou argumentos.

Arquivos exigidos dentro do container:

- `/config/config.json`: JSON não secreto gerado por `configure`, montado read-only.
- `/run/secrets/lg_pat`: PAT LG, arquivo regular ASCII, 0400 ou 0600, máximo 16 KiB.
- `/run/secrets/api_token`: chave independente da API, mesmas restrições, mínimo 32 caracteres.

O leitor rejeita symlink final, diretório, permissões abertas e conteúdo vazio/inválido.
O container não muda permissões nem proprietário. Compose fora de Swarm **ignora
uid/gid/mode para secrets baseados em arquivo**; a primeira validação revelou esse comportamento; os campos sem efeito foram
removidos do Compose final.
Prepare os arquivos para que UID 10001 consiga lê-los sem abrir leitura a grupo/outros;
considere o mapeamento de UID caso use rootless/user namespaces. Se não forem legíveis,
o serviço falhará explicitamente. Nunca resolva com chmod 0644. O JSON pode ser copiado
do desktop, mantendo client ID estável para esta instalação central; após migrar,
evite manter dois backends LG ativos desnecessariamente.

Os comandos abaixo são para execução deliberada posterior no homelab. As variáveis
contêm **caminhos**, nunca tokens. Use caminhos absolutos para os três arquivos externos:

```sh
export LG_CONFIG_FILE=/caminho/privado/config.json
export LG_PAT_FILE=/caminho/privado/lg_pat
export LG_API_TOKEN_FILE=/caminho/privado/api_token
# Confere o manifesto; não lê o conteúdo dos segredos nem inicia serviço.
docker compose -f packaging/docker/compose.yaml config --quiet
# Build e execução somente quando o operador decidir implantar:
docker compose -f packaging/docker/compose.yaml build
docker compose -f packaging/docker/compose.yaml up -d
```

O compose publica **127.0.0.1:8765** no host. O processo dentro do container escuta
0.0.0.0:8765 com HTTP interno explicitamente permitido, porque a conexão pelo bridge
Docker tem endereço de origem privado em vez de loopback. **Não altere o bind publicado
para 0.0.0.0 nem exponha a porta diretamente.** Configure proxy HTTPS no host (ou
rede privada dedicada com política equivalente) e mantenha essa etapa separada.
Clientes usam o endereço HTTPS do proxy, por exemplo `https://homelab.example:443`;
para IP literal o certificado precisa conter esse IP. O token API é obrigatório mesmo
no trecho interno Docker. O healthcheck indica apenas processo, não compatibilidade LG.

Não há restart automático configurado no compose para evitar ativação permanente
implícita nesta preparação. A API central inicia com controle real bloqueado por padrão. Para disponibilizar
os controles aos clientes autenticados, adicione `"allow_control": true` ao JSON
não secreto `/config/config.json`, reconstrua a imagem e recrie o container.
Não coloque PAT nesse JSON. O campo ausente ou `false` mantém somente leitura.
Para encerrar/remover containers posteriormente: `docker compose -f
packaging/docker/compose.yaml down`. Esse comando preserva arquivos externos de
configuração/segredos; revogue os tokens separadamente ao descomissionar.

Fontes Docker: [secrets no Compose](https://docs.docker.com/compose/how-tos/use-secrets/),
[semântica de serviços/secrets](https://docs.docker.com/reference/compose-file/services/)
e [contexto de build e dockerignore](https://docs.docker.com/build/concepts/context/).

Validação desta etapa: Docker 29.9.1 e Compose 5.6.0 presentes. `docker compose config
--quiet` passou com caminhos sintéticos, e o manifesto final não declara uid/gid/mode ignorados fora de Swarm. 45 testes pytest passaram, incluindo 9 testes HTTP loopback e 3 testes de
secret mounts/controle bloqueado. Ruff passou nos módulos/testes novos. Build da imagem e smoke test HTTP autenticado com simulação passaram. Proxy TLS,
rede do homelab, provisionamento de secrets e leitura LG no container permanecem
pendentes de validação no ambiente alvo.


## Conectar o KDE ao servidor

No computador KDE, cadastre somente a chave API do homelab no cofre, por entrada
oculta, e salve a URL não secreta (substitua o exemplo pelo HTTPS real):

```sh
export PYTHON_KEYRING_BACKEND=keyring.backends.SecretService.Keyring
.venv-runtime/bin/python -m lgthinq_daemon api-credential-set
.venv-runtime/bin/python -m lgthinq_daemon --endpoint https://homelab.example configure
.venv-runtime/bin/python -m lgthinq_daemon status
.venv-runtime/bin/python -m lgthinq_daemon serve
```

O JSON suporta `endpoint` opcional sem usuário/senha na URL. Endpoint explícito na CLI
prevalece sobre o salvo. O modo remoto não solicita PAT LG e não importa o SDK no
cliente. Para instalação leve: extras `remote,credentials`; bindings D-Bus são do host.
A unidade do KDE gerada por prepare_deploy usa esse JSON, portanto inicia a ponte
remota quando endpoint estiver salvo. Reinicie somente essa ponte ao mudar a URL.
O perfil pode desabilitar controles; a chave API não habilita escrita real: essa escolha pertence à configuração do servidor.

O menu do widget contém aparência e orientações de conexão/credenciais. A URL pertence
ao backend compartilhado, e não a uma instância isolada do widget.


Smoke test reproduzível da imagem final, sem rede externa ou PAT:

```sh
scripts/publish_image.sh --build-only
```

Resultado local: PASS; container removido ao encerrar. O script prepara um certificado
sintético descartável e testa a imagem efetiva com servidor simulado, 401 sem chave,
comando confirmado com chave sintética e validação TLS. Não testa secrets reais nem
acessa LG. Execute a suíte conforme TESTING.md para obter resultados no seu ambiente.

Ao trocar PAT ou chave API, reinicie o container depois de atualizar o secret externo;
as credenciais são mantidas em memória durante a execução, sem promessa de hot reload.

## Instalação assistida com imagem Docker Hub e HTTPS direto

Esta variante substitui o proxy externo por TLS no próprio container. O usuário
escolheu imagem pública `localhost/lgthinq`, Linux amd64, certificado local e
reinício automático. O Compose anterior continua como alternativa para proxy.
Não exponha o Compose HTTP anterior à LAN. No instalador novo a porta publicada
aceita **somente HTTPS**, em todas as interfaces do host; restrinja seu acesso aos
clientes da LAN no firewall/rede. O instalador não modifica o firewall.

### Publicar a imagem neste computador

Procedimento histórico **suspenso**. O script `scripts/publish_image.sh` existe,
mas não deve ser executado para publicação enquanto os gates de conformidade
estiverem abertos. Uma decisão futura do mantenedor é necessária para retomar.

O caminho histórico publicava tags `homelab-AAAAmmdd-HHMMSS` (UTC) e `latest`.
Na revisão final esse caminho foi desativado: o script só aceita `--build-only`,
que constrói amd64 e executa smoke HTTP/TLS com aparelho e chave sintéticos.
Invocação sem argumentos falha antes de chamar Docker. Docker e OpenSSL precisam
estar instalados para o build local. Retomar publicação exige resolver os gates
e revisar explicitamente o script; não há uma opção de bypass.
A imagem contém fontes do backend, o que não substitui a definição de direitos
nem a entrega de avisos e fontes correspondentes dos demais componentes.

### Executar no home lab

Copie **somente** `scripts/install_homelab.sh` para o servidor. O script é autônomo;
não precisa de clone, Python do projeto, SDK LG no host nem arquivos secretos deste
computador. Use terminal privado interativo, sem `tee`, captura de sessão ou pipes.

Pré-requisitos: Linux amd64, Docker convencional sem rootless/userns, Compose,
Bash, Python 3 e OpenSSL. Execute como root na sessão administrativa do home lab:

```sh
bash ./install_homelab.sh
```

Não execute como root no KDE. O instalador não executa sudo, não instala ferramentas
nem configura serviços do host. Os arquivos ficam em `/opt/lgthinq` por padrão;
`--directory /outro/diretorio` seleciona um caminho com ancestrais pertencentes ao
root, sem escrita por grupo/outros. O diretório pai deve existir. Diretórios existentes
exigem permissões privadas e arquivos reconhecidos pelo instalador.

O assistente solicita:

1. IP/nome LAN do servidor e porta HTTPS (8765 por padrão). Nome deve resolver no KDE.
2. País LG (BR), índice do aparelho (0) e permissão de controle (padrão não).
3. Confirmação explícita do armazenamento em arquivo no servidor e PAT LG oculto.
4. Ao final, opção de mostrar o token API independente para copiar ao cofre do KDE.

O IP/nome entra no SAN do certificado; mantenha endereço estável ou renove depois.
O certificado dura um ano, a CA local dez anos. O UUID é persistido. A imagem é
baixada e fixada por digest no Compose. `restart: unless-stopped` faz o container
voltar com o Docker, salvo se você o tiver parado deliberadamente.

PAT e token ficam em `secrets/` com arquivos 0600 e proprietário UID 10001. A chave
privada TLS também pertence ao usuário do container; a chave da CA fica restrita ao
root. Diretório da instalação é 0700. Isso é **armazenamento explícito em arquivo**,
sem criptografia de cofre. Proteja o disco/backups do host; não copie esses arquivos
para Git, chat ou computador cliente. O instalador recusa rootless/userns em vez de
abrir permissões. Não solucione falhas com chmod 0644 nos secrets.

O resultado inclui `compose.yaml` (JSON válido como YAML), `config.json`,
`installation.json`, `ca/`, `tls/`, `secrets/` e `KDE.txt`. O guia não contém tokens.
Healthcheck verifica TLS e processo; o instalador também consulta snapshot autenticado
sem imprimir dados privados. Falha LG não é Go operacional nem falha de certificado.
Nunca envia comandos de controle para validar a instalação.

### Conectar o KDE

Siga o `KDE.txt` impresso pelo instalador. Copie apenas `ca/ca.crt` para
`~/.config/lgthinq-kde/homelab-ca.crt` no KDE. Confirme a origem desse certificado
por seu canal administrativo confiável; nunca copie `ca.key`, `server.key` ou PAT.
A confiança fica limitada à ponte Python por `SSL_CERT_FILE`, sem alterar o cofre
global de certificados do sistema. Não há bypass de verificação TLS.

No terminal KDE, na pasta do projeto, substitua o endpoint pelo endereço impresso:

```sh
export SSL_CERT_FILE="$HOME/.config/lgthinq-kde/homelab-ca.crt"
export PYTHON_KEYRING_BACKEND=keyring.backends.SecretService.Keyring
.venv-runtime/bin/python -m lgthinq_daemon api-credential-set
.venv-runtime/bin/python -m lgthinq_daemon --endpoint https://192.168.1.50:8765 configure
.venv-runtime/bin/python -m lgthinq_daemon status
.venv-runtime/bin/python -m lgthinq_daemon serve
```

Use o **token API**, nunca o PAT, no prompt do cofre. Confira `connection`/`error`
no status. Pare o backend local anterior antes de iniciar a ponte; pode ser necessário
parar a unidade `lgthinq.service` se ela já estiver ativa. IP/porta pertencem ao
endpoint da ponte; o menu do widget não recebe o token. Instalação do pacote e adição
à barra estão no guia gerado e em [DEPLOY](DEPLOY.md).

Para a ponte permanente, valide primeiro em primeiro plano. Depois adicione à seção
`[Service]` da unidade gerada a linha abaixo, com caminho absoluto do usuário real,
antes de instalar/ativar a unidade conforme DEPLOY:

```ini
Environment=SSL_CERT_FILE=/CAMINHO/ABSOLUTO/.config/lgthinq-kde/homelab-ca.crt
```

O cofre precisa estar disponível na sessão KDE. Reinicie somente a ponte ao mudar
endpoint/certificado; não precisa reiniciar Plasma para uma alteração de conexão.

### Manutenção

Como root no home lab:

```sh
docker compose -f /opt/lgthinq/compose.yaml ps
docker compose -f /opt/lgthinq/compose.yaml stop
docker compose -f /opt/lgthinq/compose.yaml start
# Atualizar imagem/configuração; confirme a reconfiguração quando solicitado:
bash ./install_homelab.sh --image localhost/lgthinq:latest
# Renovar certificado do servidor, preservando CA, UUID, PAT e token:
bash ./install_homelab.sh --renew-cert
# Mostrar somente o token API no terminal privado:
bash ./install_homelab.sh --show-token
```

Reexecução preserva os secrets e pede confirmação antes de reconfigurar. Mudança de
IP/nome exige `--renew-cert`. O controle é perguntado novamente e continua opt-in.
Para rollback, informe `--image localhost/lgthinq@sha256:DIGEST_ANTERIOR`.
`docker compose down` remove o container/rede e preserva os arquivos da instalação.
Para trocar PAT/token, atualize o secret correspondente por procedimento privado,
preservando proprietário/permissões, e recrie o container (`up -d --force-recreate`),
pois a troca atômica do arquivo requer remontagem. Recadastre o token nos clientes
se ele mudar. Falhas preservam os arquivos para diagnóstico; uma atualização que
falhe pode exigir rollback manual. Não imprima logs privados ou snapshot bruto em
relatórios compartilhados.
