# Regularização da imagem Docker existente

Referências de imagem usam `localhost/lgthinq` como identificador local
anonimizado; não indicam um registry público disponível.

**Pendente; não publicar, substituir, retaggear ou recomendar nova redistribuição.**
Esta etapa não executa operação no registry e não declara conformidade.
`scripts/publish_image.sh` recusa publicação antes de invocar Docker. Somente seu
modo explícito `--build-only` continua disponível; ele não foi executado nesta revisão.

Referência histórica: `localhost/lgthinq:homelab-20261023-155724`, também publicada
como latest. Digest imutável auditado:
`sha256:ee70819f11d322e3e31399acda5c3209c5b908bb647872414501fa08eca37623`.
Tags são mutáveis; a referência para a regularização é o digest, não latest.
O inventário abaixo é evidência histórica, sem nova extração da imagem ou consulta
ao registry nesta preparação. Não equivale a uma verificação atual de conformidade.

## Inventário histórico da auditoria

| Camada/conjunto | Versões observadas | Estado |
|---|---|---|
| Código do projeto | metadata 0.1.0; checkout atual 0.2.0 | Sem licença concedida e sem vínculo de revisão OCI; imagem não equivale ao checkout |
| CPython / Debian | Python 3.14.9; Debian 13.7 trixie | Licenças PSF e por pacote; 85 arquivos Debian copyright localizados |
| GNU Bash / coreutils | 5.2.37-2+b10 / 9.7-3 | GPLv3+ predominante; fonte correspondente e termos por arquivo a revisar |
| glibc | 2.41-12+deb13u4 | LGPLv2.1+ predominante, com diversos componentes/licenças |
| OpenSSL | 3.5.7-1~deb13u3 | Apache-2.0 predominante; copyright por arquivo |
| Dependências Python | thinqconnect 1.0.14, aiohttp 3.14.5, awsiotsdk 1.31.0, awscrt 0.36.1, cryptography 50.0.2 e transitivas | Ver [DEPENDENCIES](DEPENDENCIES.md); natives ainda não integralmente revisados |
| pip e conteúdo vendorizado | pip 26.2.2; várias bibliotecas internas | Avisos encontrados; não é um conjunto exclusivamente MIT |

O arquivo Dockerfile usa base mutável `python:3.14-slim` e instalação pip com
transitivas abertas. Reexecutá-lo hoje não reproduz necessariamente esse digest.
O kernel Linux do host não foi demonstrado como conteúdo da imagem.

Os materiais locais de agentes/ai-memory permanecem no checkout privado, fora do
futuro snapshot público e dos payloads atuais do produto. Sua presença local não
cria obrigação de avisos ai-memory na imagem: isso depende de redistribuição efetiva.
A imagem histórica e seus terceiros devem ser avaliados pelos bytes incorporados;
excluir arquivos do snapshot futuro não regulariza o digest anterior.

## Lacunas

- Direitos e licença do código próprio, fonte/revisão exata do produto embarcado.
- LICENSE/NOTICE do awsiotsdk ausentes do wheel e não supridos explicitamente pelo build.
- Inventário de bibliotecas C/Rust e demais componentes incorporados aos wheels.
- Revisão pacote a pacote da base Debian e licenças vendorizadas do pip, incluindo
  certifi/MPL-2.0, além dos avisos Apache/MIT/BSD.
- Mecanismo comprovado de entrega de fonte correspondente dos componentes GPL/LGPL,
  incluindo versões, patches e scripts de build necessários. Link genérico para
  Debian ou código Python em `/app` não comprova o cumprimento desse conjunto.
- Dockerignore não permite incluir futuros LICENSE/NOTICE sem alteração explícita.

## Procedimento proposto, sem execução remota

1. Preservar a identificação do digest e inventariar conteúdo/versões em leitura,
   sem executar o serviço LG nem recolher secrets de containers em uso.
2. Relacionar cada binário à fonte exata e aos termos aplicáveis; gerar SBOM e mapa
   de avisos, incluindo subcomponentes. Resolver ausências antes de novo build.
3. Definir com o mantenedor a modalidade de cumprimento de fonte correspondente
   adequada à distribuição feita, conservando fontes/patches verificáveis. A
   [orientação Debian](https://www.debian.org/doc/manuals/debian-faq/redistributing.en.html)
   não elimina as obrigações do redistribuidor.
4. Após liberação de direitos, preparar correções locais: textos legais completos,
   payload/labels coerentes, base e resoluções registradas e acesso à fonte exata.
5. Revisar e testar localmente sem LG. Só publicar uma imagem corrigida com nova
   autorização explícita. Corrigir tags não altera nem regulariza retroativamente
   os bytes já distribuídos sob o digest antigo.

## Opções que exigem decisão do mantenedor

- Manter a distribuição suspensa e, após análise, disponibilizar documentação,
  avisos e fontes correspondentes ao digest antigo onde essa modalidade satisfizer
  as licenças aplicáveis. Não presumir que suplemento cure toda lacuna.
- Retirar de circulação tags/artefatos problemáticos, se apropriado; isso exige
  autorização e não desfaz cópias anteriores ou obrigações já existentes.
- Publicar futuramente novo digest corrigido, mantendo referência clara à versão
  substituída e às limitações da distribuição anterior.

Nenhuma das opções foi executada. A escolha depende de direitos confirmados e da
análise dos componentes efetivamente redistribuídos, não apenas da licença do backend.

## Inspeção independente local de 2026-10-23

O digest acima foi encontrado no cache local e exportado de um container criado
exclusivamente para inspeção, sem start, rede ou mounts. O container temporário foi
removido após exportar; nenhuma imagem/tag foi alterada. Não houve pull, build ou push.
Os resultados abaixo são observações daquela inspeção do rootfs local, distintas do quadro
histórico. Um `docker image save` também preservou as oito camadas; seus nomes de
arquivos foram inspecionados, incluindo paths de avisos, fontes e arquivos privados.
Isso não equivale a procurar segredos no conteúdo integral de todos os arquivos.

- ID local: `sha256:d700d898f0ee2240c55cb6e9af30fbe43550adc76a914612a2ec8258a7f9eb8d`;
  amd64, oito camadas. Não há labels OCI de fonte/revisão/licença nem digest da base.
- CPython 3.14.9 e Debian 13.7 trixie confirmados por ENV/history e os-release.
  O history registra snapshot Debian e hash do tarball CPython, mas isso não
  comprova por si a origem assinada, o digest da base ou a correspondência binária.
- 87 pacotes Debian instalados; todos têm copyright acessível após resolver
  aliases/symlinks internos. Identidades Source/Version e termos declarados foram
  inventariados; entrega de fontes/patches exatos ainda não comprovada.
- 17 distribuições Python, incluindo o próprio projeto em 0.1.0. A imagem contém
  fontes diferentes do checkout 0.2.0; não a tratar como build desta revisão.
- 171 arquivos de avisos/licenças inventariados. `awsiotsdk` 1.31.0 não tem
  LICENSE/NOTICE instalado. Os dois documentos da tag upstream foram adquiridos
  para evidência externa, sem modificar ou regularizar retroativamente a imagem.
- 757 arquivos ELF inventariados; 12 pertencem aos wheels. readelf foi usado nos
  12 e no executável/libpython, sem executar esses binários. A ausência de uma
  biblioteca em DT_NEEDED não exclui incorporação estática: CRT, TLS, Rust e demais
  componentes ainda exigem mapa de build/fontes e avisos por subcomponente.
- Não foram encontrados nomes `.env`, `credentials.json`, `/run/secrets/` ou
  `/config/` no rootfs inspecionado. Isso não é varredura conclusiva de segredos,
  ou de conteúdo arbitrário. A mesma busca por nomes nas oito camadas também
  não encontrou esses candidatos.

O relatório externo contém hashes, inventários de arquivos/pacotes, textos legais,
linkage e comparação de fontes. Smoke HTTP/TLS com clientes e certificado sintéticos
passou na imagem em cache com `--pull=never --network none`, entrypoint substituído
pelo teste, rootfs read-only e sem capabilities. Não iniciou o serviço LG.
Permanecem bloqueados: direitos próprios,
correspondência de fontes/binários, obrigações dos nativos, mecanismo de entrega
de fonte e decisão sobre a distribuição histórica. A orientação oficial
[Debian sobre redistribuição](https://www.debian.org/doc/manuals/debian-faq/redistributing.en.html)
exige respeitar as licenças de cada componente; não há aprovação jurídica nesta revisão.

## Gates e investigação desta execução

Publicação e provisionamento são operações distintas. `publish_image.sh` continua
recusando qualquer publicação antes de Docker; seu modo build-only é ensaiado com
Docker falso. `install_homelab.sh` agora recusa execução normal, inclusive image,
renew-cert e show-token, antes de Python, prompts, segredo, pull ou deploy.
Somente help é informativo. Não há flag/variável de ambiente de liberação. O motor
antigo permanece preservado e é testado com dependências sintéticas; não é um
caminho de implantação habilitado. Compose continua um descritor de build/deploy
local e não é protegido por esse script; nesta fase não deve ser executado.

O inventário estático `scripts/audit_distribution.py docker-plan --output CAMINHO_NOVO`
registra FROM/COPY/RUN, hash do Dockerfile, ausência de digest e labels. Não executa
Docker. O contexto seleciona pyproject/BACKEND/MANIFEST e módulos; não inclui UI,
agentes ou futuros avisos. A base continua python:3.14-slim, sem apt adicional;
base e pip transitivo não fixados, sem labels OCI. Fixar um digest ou versão sem
obter e testar a resolução exata daria falsa reprodutibilidade: ficou pendente.

Há avanço de fontes em [NATIVE_COMPONENTS](NATIVE_COMPONENTS.md): 13 gitlinks CRT,
LICENSE/NOTICE fixados e candidatos Rust. Isso não certifica o wheel da imagem.
Reutilizar os inventários preservados do digest, 87 pacotes Debian, 17 distribuições
Python, 171 avisos e 757 ELF; seus hashes/referências foram reconferidos sem executar,
extrair novamente ou alterar a imagem. Não houve Docker build, pull, push, login
nem consulta autenticada a registry. Metadata pública adicional não era necessária
para confirmar a diferença histórica 0.1.0/0.2.0.

Para uma futura imagem: obter digest/plataforma da base realmente escolhida,
resolução pip/hashes, origens de pacotes Debian com patches e scripts, revisões
CPython, libcrypto/CRT/Rust e vendorizados pip; conservar fontes e avisos com
mecanismo de entrega adequado revisado pelo responsável. Labels source/revision,
version e licenças somente após valores reais e direitos confirmados. A lista de
[avisos por formato](ARTIFACT_NOTICES.md) não é um suplemento publicado nem corrige
retroativamente o digest histórico. A decisão de suspendê-lo, oferecer fontes/avisos
ou substituí-lo futuramente depende de confirmação humana e autorização separada.
