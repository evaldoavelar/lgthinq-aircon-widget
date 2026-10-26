# ADR-0008 — Controle real por opção explícita do operador

Status: adotada, 2026-10-22.

O backend de leitura forçava writable=false e recusava comandos em várias camadas,
sem fornecer mecanismo de liberação. O usuário exige o objetivo operacional de
controlar o aparelho pelo widget; o limite original impede testes automáticos no
hardware, não a implementação de controle para uso manual.

Adotamos `--allow-control`/`--no-allow-control` e o campo JSON booleano `allow_control`,
padrão false. CLI explícita prevalece sobre JSON. Engine limita as capacidades
expostas; LiveClient/ContainerClient e SDKClient aplicam o bloqueio antes de enviar.
No modo remoto a permissão pertence ao servidor; a ponte não eleva permissões.
Habilitar controle permite ações manuais autenticadas; não inicia comando sozinho.

Valores continuam validados contra o perfil. Payload de temperatura usa objeto com
unit conforme AirConditionerProfile._get_attribute_payload e
ConnectBaseDevice.do_multi_attribute_command no thinqconnect 1.0.14 instalado.
As listas permanecem no perfil/status, sem contaminar o formato de comando.
Depois da escrita ocorre leitura de estado, sem publicar intenção como confirmação.
Timeout não garante cancelamento físico e não causa repetição automática do comando.

A API compartilha uma chave entre clientes: todos os clientes autenticados recebem
as mesmas permissões. Não há separação por usuário/dispositivo ou ACL granular.
Testes usam fixtures sintéticas, inclusive quando simulated=false verifica políticas.
Validação física permanece separada e não é declarada aprovada.

Atualização: polling de estado em 15s e perfil em cache por processo reduzem espera e
requisições repetidas. Abrir popup pode solicitar Refresh, respeitando cache de 5s.
Uma leitura do cache D-Bus a cada 5s complementa os sinais sem fazer rede no QML.
Refresh explícito na ponte remota usa request_refresh; polling automático continua
consultando cache HTTP. Isso evita multiplicar chamadas LG por cliente; não é push.
