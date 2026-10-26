# ADR-0007 — Backend central Docker e clientes independentes

Referências de imagem usam `localhost/lgthinq` como identificador local
anonimizado; não indicam um registry público disponível.

- Estado: implementado e testado localmente com simulação; deploy real pendente.
- Contexto: usuário escolheu servidor no homelab via Docker, acessível por IP/nome,
  compartilhável por KDE e um futuro cliente Windows. O popup deve seguir a referência
  visual fornecida, sem reproduzir capacidades ou limites fictícios.
- Decisão: API HTTP versionada /v1, snapshots compatíveis com o contrato D-Bus e
  autenticação por chave própria do projeto, diferente do PAT LG. Polling central
  evita multiplicar chamadas LG. O KDE mantém ponte Python local para D-Bus; QML não
  recebe PAT nem se conecta diretamente à LG. Windows poderá consumir a mesma API.
- Transporte: HTTPS fora de loopback. Docker publica porta somente em loopback do
  host, para terminação TLS externa. HTTP interno Docker é deliberado, sem inferir
  confiança em cabeçalhos encaminhados. Não há autorização para publicar na LAN/internet.
- Segredos: desktop usa cofre. Variante Docker usa EXPLICITAMENTE secrets montados em
  runtime, fora do Git/imagem, sem fallback. Bind mounts Compose não criptografam
  o disco do host; secret manager/Swarm ou proteção do host cabem ao operador.
- Deploy: imagem local e compose preparados; unidade systemd do KDE executa somente a
  ponte local. Gerador cria .plasmoid/unidades sem instalar. Ativação é separada.
- Interface: indicador compacto no painel e popup escuro QML, ilustração vetorial
  original, cartões derivados do perfil e valores confirmados. Configuração Plasma
  só armazena aparência; conexão e URL ficam no JSON não secreto do backend.
- Limites: uma chave API compartilhada nesta versão, sem ACL por cliente; cliente
  Windows não implementado; LG real continua somente leitura. Testes simulados não
  aprovam comandos LG nem comprovam rede/certificado/cofre do homelab.

## Extensão autorizada — 2026-10-23 (registro histórico)

A autorização abaixo registra a decisão daquela etapa. Foi superada pela suspensão
atual de publicação/redistribuição: veja [LICENSING](../LICENSING.md) e o
[gate Docker](../DOCKER_COMPLIANCE.md). Não autoriza nova imagem, tag, push ou deploy
nesta fase; retomar publicação exige decisão separada após resolver os gates. Os
arquivos locais de agentes/contexto continuam no checkout privado e ficam fora do
futuro snapshot público e dos pacotes; seus avisos só se aplicam se redistribuídos.

Usuário escolheu publicação pública `localhost/lgthinq` para Linux amd64 e
instalador autônomo com Compose, PAT oculto, certificado local para IP/nome, token
API e instruções KDE. Autorizou reinício automático; controle continua pergunta
explícita com padrão não. O novo Compose publica HTTPS direto no container na
porta escolhida, em todas as interfaces do host para acesso LAN; não autoriza
exposição à internet. O modo antigo HTTP com bind loopback/proxy permanece separado.

Container aceita `--tls-cert` e `--tls-key` em par; falha de TLS interrompe startup.
Sem argumentos mantém o modo HTTP interno anterior. Instalador cria CA local,
certificado SAN de um ano e arquivos privados externos ao Git; imagem fixa por
digest, processo UID 10001 e proteções do Compose preservadas. Docker rootless e
userns são recusados para evitar remapeamento incorreto de permissões.

Cliente KDE confia na CA somente no processo da ponte via `SSL_CERT_FILE`; token
API continua em Secret Service/KWallet. Instalador não muda confiança global nem
configura o KDE remotamente. Publicar a imagem não valida LG, rede LAN, cofre ou
controle físico. O operador executará o deploy no home lab e a validação manual.
