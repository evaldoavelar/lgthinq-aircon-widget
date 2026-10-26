# Contrato D-Bus

Requer o módulo QML `org.kde.plasma.workspace.dbus` com `SignalWatcher`.
O piso de API identificado é Plasma Workspace 6.4; runtime completo só exercitado
no host 6.8/Qt 6.12. Fonte por tag e limites em [COMPATIBILITY](COMPATIBILITY.md).

Bus de sessão; serviço `org.lgthinq.LGThinq`; objeto `/org/lgthinq/LGThinq/AirConditioner`.
PoC e produção não podem possuir esse nome simultaneamente. Outro processo proprietário
faz a inicialização falhar, sem substituir o serviço existente.

## Produção — `org.lgthinq.LGThinq.AirConditioner1`

| Membro | Entrada | Saída | Semântica |
|---|---|---|---|
| GetSnapshot | — | s | JSON do último snapshot publicado; não faz rede |
| Refresh | — | b | aceita consulta assíncrona; false se já ocupado |
| Command | ss | b | chave de capacidade + valor JSON; aceita tarefa, não confirma resultado |
| SnapshotChanged (sinal) | s | — | JSON completo, incluindo transição e resultado confirmado |

Snapshot contém `connection`, `state`, `capabilities`, `updated_at` (Unix, segundos,
null antes da leitura), `error` (categoria ou null), `simulated`. Capacidades têm
`path` (array), `writable` (autorização efetiva), `supported_writable` (suporte declarado pelo perfil), `values`, `minimum`, `maximum`, `step`, `unit`, `excluded`.
`unit` é string ou null, inclusive quando o perfil a declara como enum legível de
valor único. Enum ambíguo não recebe unidade presumida. Chaves com representação
de dicionário eram um bug, corrigido sem alterar a interface D-Bus.
Valores ausentes são null ou ausentes; UI não deve preenchê-los com defaults.
`state` preserva recursos do protocolo LG nesta primeira versão; nomes das chaves de
capacidade são caminhos unidos por ponto, com sufixo de unidade quando houver.
Isso ainda exige teste contra perfis reais antes de congelar um modelo universal.

Estados: `disconnected`, `connecting`, `connected`, `auth_required`,
`command_pending`, `error` (falha normalizada), `operational_error` (falha da ponte).
`error` pode indicar rede, região, ausência, falta de suporte, limite de chamadas ou
operação. Comando inválido nunca modifica o estado confirmado. Aceitação da fila
não promete que o comando será validado: aguarde sinal final. Uma tarefa por vez,
sem fila ilimitada. JSON inválido é rejeitado imediatamente.

A ponte usa chamadas não bloqueantes no QML; rede em asyncio dedicado. Publicações
vêm ao GLib via idle callback. Polling nominal 15s; falha dobra espera até 900s;
autenticação suspende polling automático. Refresh manual permite nova tentativa.
A UI detecta desaparecimento e reaparecimento por DBusServiceWatcher. O serviço não devolve PAT em consultas ou sinais. A interface Configuration1
recebe credencial transitória para armazenamento no cofre. Controle real é liberado com `--allow-control` ou configuração `allow_control: true`
no servidor. Sem essa opção, `writable=false` mesmo quando `supported_writable=true`.
A UI distingue permissão de escrita de indisponibilidade temporária durante polling/comando.

## Configuração local — `org.lgthinq.LGThinq.Configuration1`

Mesmo serviço/objeto da produção. Acrescenta, sem alterar AirConditioner1:

| Membro | Entrada | Saída | Semântica |
|---|---|---|---|
| GetSettings | — | s | cache JSON de opções não secretas e resultado de descoberta |
| Configure | ss | b | JSON de opções + PAT transitório; aceita tarefa, não confirma sucesso |
| Discover | — | b | nova descoberta usando opções/cofre já cadastrados |
| ConfigurationChanged (sinal) | s | — | opções, busy e erro normalizado após transições |

Configure aceita country, device_id, allow_control e convert_to_local. PAT vazio
mantém o segredo existente; não há método para ler PAT. JSON desconhecido/inválido
é recusado sem imprimir conteúdo. Limites de entrada: JSON 8192 caracteres e PAT
16384. A mesma exclusão de tarefas do serviço serializa configuração/rede/comandos.
GetSettings não acessa rede/cofre. O resultado contém country, device_id,
allow_control, remote, devices (id/label), busy e error; IDs/aliases são privados
da sessão e não pertencem a logs compartilhados. Backend legado/simulado sem
controlador de configuração devolve unsupported=true.

Configure valida opções, guarda credencial no cofre quando fornecida, persiste JSON
sem segredo, recria sessão e descobre aparelhos. Cadastro do cofre e gravação do JSON
não são transação distribuída: após falha de disco, o operador pode precisar salvar
novamente. Troca de país descarta seleção anterior. ID desconhecido exige descoberta
prévia. Endpoint existente só é removido com convert_to_local=true explícito.

Antes do cadastro, snapshot usa disconnected/error=setup_required. Polling automático
não consulta LG nesse estado; Configure/Discover retomam o fluxo. Autenticação pausa
polling, substituição do PAT recria o cliente. O serviço local pode ser iniciado sem
configuração com serve-local. O instalador registra D-Bus/systemd; não habilita unidade
em boot. O widget solicita ativação ao carregar e limita novas tentativas de falha.

O D-Bus da sessão não isola aplicativos do mesmo usuário e permite observação local;
não é um canal contra comprometimento da sessão. Segredos não vão a argumentos,
KConfig, respostas, sinais, arquivos de configuração ou logs do projeto.

## PoC — `org.lgthinq.LGThinq.AirConditioner`

| Membro | Entrada | Saída |
|---|---|---|
| GetTemperature | — | d |
| GetPower | — | b |
| SetTemperature | d | b |
| SetPower | b | b |
| StateChanged (sinal) | db | — |

Propriedades somente leitura `targetTemperature:d` e `power:b` via interface padrão
`org.freedesktop.DBus.Properties.Get/GetAll`, com `PropertiesChanged(sa{sv}as)`.
Setters são métodos explícitos. Limites 10–35 são exclusivamente sintéticos.
`--demo-tick` gera atualização independente a cada 5s. Teste local de introspecção
valida XML, tipos e assinaturas; transporte sintético demonstrado no plasmoidviewer por automação; veja o registro
histórico no [ADR-0006](decisions/ADR-0006-runtime-validation.md) e como repetir em
[TESTING](TESTING.md). Isso não valida LG real ou aceitação humana.

Fonte do mecanismo QML: [DBusConnection KDE](https://github.com/KDE/plasma-workspace/blob/master/components/dbus/dbusconnection.h)
e [SignalWatcher KDE](https://github.com/KDE/plasma-workspace/blob/master/components/dbus/dbussignalwatcher.h).
Método usa assinatura entre parênteses, por exemplo `(ss)`; handler do sinal é
`dbusSnapshotChanged`. API instalada em Plasma Workspace 6.8.0 foi conferida no
arquivo `dbusplugin.qmltypes`.

A partir do widget 0.1.3, cada transição de fechado para aberto solicita Refresh,
inclusive com snapshot recente. Ocupação/indisponibilidade adia a solicitação até o
serviço ficar livre, desde que o popup continue aberto; fechar descarta a solicitação.

O widget 0.1.4 mantém seleção de temperatura local durante edição e agrupa passos por
700ms. Somente o valor final vira Command. Seleção não modifica snapshot nem indicador
do painel. Aceitação de Command não encerra espera: requer snapshot conectado com
updated_at posterior à submissão. Em erro, não há retry automático da escrita.

No controlador integrado remoto, `Refresh` encaminha uma única solicitação ao
`RemoteEngine.request_refresh()` (POST /v1/refresh). O polling do backend usa
`refresh()` (GET /v1/snapshot em cache); `GetSnapshot` só lê cache local. Ambos
executam no worker assíncrono e preservam a política de erros do RemoteEngine.
