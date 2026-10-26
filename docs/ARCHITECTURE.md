# Arquitetura

Situação atual: produto local integrado em desenvolvimento, conforme ADR-0010;
distribuição pública autorizada conforme [licenciamento](LICENSING.md). Os ADRs e seções
datadas preservam decisões históricas. Requisitos: [COMPATIBILITY](COMPATIBILITY.md).
Distribuição do widget e backend: [DISTRIBUTION](DISTRIBUTION.md).

## Produto local integrado (ADR-0010)

O caminho principal instala widget e componente Python como um produto no usuário.
O componente é ativado pelo D-Bus de sessão usando `lgthinq-local.service`, sem
`enable` nem servidor HTTP. Reinício de falhas é limitado; configurações gráficas
funcionam antes de existir PAT ou seleção de aparelho. O controlador local gerencia
reconfiguração, descoberta e recriação das sessões sem reinício manual.

O PAT transita temporariamente do campo oculto para o componente pelo D-Bus e fica
persistido exclusivamente no cofre. A interface não o consulta de volta. Operações
de cofre/discovery/rede executam fora da thread de renderização. Configuração não
secreta mantém UUID e ID do aparelho; o perfil continua definindo capacidades.
Homelab permanece opcional e Windows é futuro. Veja [instalação](INSTALL.md).

## Visão de destino

```text
LG ThinQ Connect API / SDK
          │ HTTPS + eventos, se necessários
          ▼
Serviço Python (processo de usuário)
  ├─ autenticação e credenciais
  ├─ descoberta/status/capacidades
  ├─ validação de comandos e máquina de estados
  └─ sanitização de logs
          │ D-Bus de sessão (IPC local)
          ▼
Plasmoid KDE Plasma 6 (QML)
  ├─ apresentação do estado
  ├─ controles baseados nas capacidades
  └─ feedback de carregamento/erro/offline
```

## Responsabilidades

### Serviço Python

- Possuir toda comunicação com a nuvem; a UI não realiza chamadas de rede externas.
- Controlar leitura, comandos, timeout, reconexão e atualização do estado.
- Expor interface estável por D-Bus, com sinais de mudança.
- Recuperar-se de falhas sem derrubar o Plasma Shell.
- Não registrar PATs, cabeçalhos de autenticação nem respostas privadas brutas.

### Plasmoid

- Exibir o estado confirmado recebido pelo D-Bus.
- Não tratar clique como confirmação de sucesso: esperar resposta do serviço/novo estado.
- Ocultar/desabilitar controles que não sejam suportados pelo perfil confirmado.
- Deixar claro quando status estiver indisponível ou desatualizado.
- Não efetuar I/O de rede no loop de renderização.

## Princípios

1. Primeiro provar; depois generalizar.
2. Separar PoC de produção.
3. Interfaces internas versionáveis e documentadas.
4. Nenhum controle fictício apresentado como estado real.
5. Preservar mudanças existentes e validar correções com dados sintéticos.

## Implementação atual (2026-10-22)

- `client.py`: protocolo injetável, SDKClient com serialização/timeout e SimulationClient.
- `live.py`: sessão HTTP criada no loop do backend, escrita somente com opt-in e fechamento explícito.
- `models.py`: Snapshot/Capability; normalizador conservador de profile.property.
- `credentials.py`: Secret Service/KWallet explícitos por keyring, entrada oculta.
- `engine.py`: consulta confirmatória, validação, estados e monitoramento.
- `dbus_service.py`: GLib no processo principal e asyncio em thread; uma tarefa aceita
  por vez, publicação por idle callback, cache JSON para GetSnapshot sem I/O externo.
- `cli.py`: descoberta sanitizada, seleção, status, credencial e serviço; escrita real exige opt-in.
- `plasmoid/`: consumidor nativo de sinais e chamadas D-Bus; sem HTTP ou subprocessos; configuração envia PAT transitório ao cofre via D-Bus.

O snapshot é estável na estrutura externa, mas state e paths ainda preservam os nomes
LG. A cobertura de perfis complexos e metadados de modelo precisa de amostras reais
sanitizadas. Não foi construída uma camada universal de eletrodomésticos. A interface
real publica writable=false enquanto controle não for especificamente autorizado.
A PoC e o daemon compartilham o nome do bus: execute apenas um. Não há MQTT ativo
nem dependência do APK para usar a rota oficial. O instalador integrado registra
ativação D-Bus/systemd sob demanda; não usa enable. A situação da sessão real não
pode ser inferida da ausência de ativação em um teste isolado. Ver ADR-0005/0010.

## Servidor central opcional (ADR-0007)

HTTP API v1 e polling central no homelab; snapshots são compartilhados com clientes.
O KDE usa RemoteEngine na ponte D-Bus existente; QML continua sem chamadas LG.
Container não requer D-Bus nem cofre gráfico: exige secrets explicitamente montados.
Cliente KDE usa cofre para chave API independente. Configuração de conexão pode ser
persistida em JSON não secreto. Transporte exige HTTPS fora do trecho interno Docker
ou loopback. Não há Windows UI implementada; contrato HTTP está documentado para ela.

## Reutilização por novas plataformas

LG ThinQ AirCon Widget mantém o núcleo sem imports Qt, QML, GLib ou D-Bus:

| Camada | Implementação e consumidores atuais |
|---|---|
| Domínio | `models.py`: capacidades, snapshot, validação conservadora do perfil; usado por Engine e UI via JSON |
| Integração LG | `client.py` (SDKClient/SimulationClient) e `live.py`: descoberta, perfil, estado e comandos assíncronos |
| Aplicação | `engine.py`: estado confirmado e autorização; `local.py`: seleção persistente, descoberta e configuração; `remote.py`: opção HTTP |
| Persistência/credenciais | `config.py`: JSON não secreto; `credentials.py`: Vault restrito a cofre; dependências injetáveis no controlador |
| KDE | `dbus_service.py`: GLib/D-Bus e worker asyncio; `plasmoid/`: apresentação e configuração QML |
| Ferramentas | `cli.py` e instalador; gettext só na apresentação; categorias JSON/D-Bus continuam estáveis |

Uma nova interface pode fornecer sessão SDK/credencial e consumir Engine/SDKClient,
ou consumir o contrato HTTP opcional. Não precisa importar `dbus_service.py` nem
componentes visuais KDE. O Vault atual é um adaptador desktop Linux: Windows terá
seu próprio cofre, ciclo de processo e instalador. GNOME terá seu adaptador visual.
Não há implementação dessas plataformas nem abstração nova sem consumidor.

## Identificadores públicos

A identidade pública e a distribuição Python passam a LG ThinQ AirCon Widget e
`lgthinq-aircon-widget`. A versão candidata é `1.0.0rc1`. O instalador cria runtimes
por versão e instala pelo caminho-fonte, sem depender do nome antigo da distribuição.
D-Bus e Plasma adotam org.lgthinq na publicação de 2026-10-26.
Instalações anteriores precisam remover o pacote antigo e reinstalar; não há
migração automática de instâncias do painel. Configuração e cofre não mudaram.

| Contrato mantido | Consumidores / motivo |
|---|---|
| `lgthinq_daemon`, CLI `lgthinq` | Scripts, entrada de runtime e unidades já instaladas |
| `org.lgthinq.LGThinq`, objeto e interfaces | UI, ativação D-Bus, PoC e clientes; namespace público neutro |
| Plasmoid `org.lgthinq.aircon` | Plasma e novas instâncias; instalações anteriores exigem reinstalação |
| `lgthinq-local.service`, diretório `lgthinq-local`, artefatos `lgthinq-local.pyz` / `lgthinq.plasmoid` | Instalador, recibo, atualização/remoção e guias existentes |
| `lgthinq-kde/config.json`, cofre `lgthinq-kde-widget` e alias `default` | Seleção, UUID e segredo existentes; renomear exigiria migração desnecessária |
| Domínios `plasma_applet_org.lgthinq.aircon` / `lgthinq-kde-widget` | Catálogos Ki18n/gettext; independentes do nome da distribuição Python |

Referências históricas a versões/decisões descrevem evidência anterior. Não ampliam
suporte a outros eletrodomésticos; o controlador local filtra `DEVICE_AIR_CONDITIONER`.
