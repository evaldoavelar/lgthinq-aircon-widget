# Segurança, credenciais e dados

## PAT

- PAT deve ser criado/copiado pelo usuário no portal oficial da LG; não solicitar nem armazenar senha da conta.
- Não colocar o PAT em prompt de agente, conversa, linha de comando visível, arquivo de configuração versionado ou log.
- A implementação usa KWallet/Secret Service pelo keyring, rejeitando backends inseguros. A validação operacional com cofre real continua pendente; não presumir que qualquer ambiente tem o cofre disponível.
- Fallback em arquivo não é automático. Se um dia for aprovado, exigir diretório `0700`, arquivo `0600`, criação atômica, verificação de permissões e aviso explícito. Isso reduz exposição local, mas não equivale a um cofre.
- Tratar HTTP 401/revogação como `AuthRequired`; não entrar em ciclos agressivos de retry.

## Logs

Sanitizar antes de serializar qualquer mensagem. Redigir pelo nome do campo (por exemplo, `pat`, `accessToken`, `refreshToken`, `Authorization`) e não depender apenas de uma regex de texto. Por padrão, mascarar também identificadores de dispositivo em diagnósticos compartilhados.

## Dados privados e arquivos grandes

- Não versionar APK, DEX, captura PCAP/HAR, dump bruto ou payload de dispositivo.
- Usar fixtures sintéticas ou sanitizadas.
- Se for necessário manter evidência privada, guardá-la fora do repositório e documentar apenas o caminho lógico, hash e conclusão sanitizada.

## Testes seguros

Automação usa somente dados sintéticos e serviços isolados. Comandos ao aparelho
exigem opção explícita de controle e validação manual pelo operador. Nunca usar
credenciais ou hardware reais em CI.

## Escopos do PAT

Não afirmar que o PAT possui escopo granular enquanto isso não estiver comprovado por documentação oficial aplicável. Descrever apenas as capacidades realmente verificadas.

## Checklist desta entrega

- [x] Sem PAT em argumentos, fixtures ou logs do projeto; entrada por getpass no cofre.
- [x] Sem fallback de credencial em arquivo/env e sem backend plaintext/chainer aceito.
- [x] Exceções SDK não são impressas com headers ou mensagens privadas.
- [x] Descoberta oculta IDs/aliases; estado compartilhado ainda exige revisão de privacidade.
- [x] CLI real, LiveClient e capacidades do daemon recusam escrita real sem opt-in.
- [x] Testes usam somente dados sintéticos; nenhum upload, comando LG ou serviço habilitado.
- [ ] Validar cofre real desbloqueado e revogação do PAT, sem registrar conteúdo.
- [ ] Validar logs e dependências efetivamente instaladas em host com rede.
- [ ] Validar acesso ao Session Bus: processos da mesma sessão podem ler estado do serviço;
  D-Bus de sessão não substitui isolamento entre aplicativos locais do mesmo usuário.

O registro de desenvolvimento declara fontes escritos localmente e ausência de
cópia do SDK; isso não comprova titularidade exclusiva. GPL-3.0-or-later para código
e CC BY 4.0 para prosa própria são preferências ainda condicionadas à confirmação
dos direitos. Imagens/marcas e conteúdo incorporado continuam separados; veja
[LICENSING](LICENSING.md) e [DEPENDENCIES](DEPENDENCIES.md). Distribuição dos materiais próprios autorizada em 2026-10-26; dependências mantêm seus termos.
## Configuração gráfica local integrada

O campo de PAT usa senha oculta sem predição de entrada e é limpo após submissão.
A credencial transita em memória via D-Bus de sessão até o cofre; não é propriedade
persistente do Plasma nem retornada por métodos/sinais. Aplicativos do mesmo usuário
podem observar o barramento: essa integração não oferece isolamento contra sessão
comprometida. Credenciais Python não têm garantia de apagamento físico de memória.

O componente seleciona Secret Service ou KWallet seguro disponível. Override
explícito continua validado; plaintext/chainer/fail não são aceitos. Erro de cofre
não cria arquivo de segredo. Instalador não acessa LG nem cofre e só prepara runtime,
widget e ativação da sessão. Índices legados só migram após descoberta válida.

## Variante Docker e clientes remotos

PAT LG pertence somente ao servidor. Chave API própria fica em namespace separado
no cofre do cliente (`lgthinq-homelab-api`); nenhuma configuração Plasma recebe segredo.
No container, files de segredo são um mecanismo EXPLÍCITO de montagem em runtime,
sem fallback do desktop. Compose local usa bind mounts, que não criptografam o disco.
Operador precisa proteger/provisionar arquivos externos ou usar secret manager/Swarm.
Não copie segredos ao build context: dockerignore permite somente fonte/metadados.
A imagem roda sem root e o compose usa read-only/no-new-privileges/cap_drop ALL.
API autentica por Bearer, valida entradas e não segue redirects no cliente. URL com
credencial é rejeitada; HTTPS verifica certificados, sem opção de ignorar TLS.
Servidor real inicia somente leitura por padrão. O operador libera comandos com
`--allow-control` ou `"allow_control": true` no JSON Docker. Uma chave API válida
não altera essa opção. Com controle habilitado, todos os clientes autenticados podem
enviar comandos permitidos pelo perfil; não há ACL granular por cliente.
