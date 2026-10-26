# Avisos por payload

Distribuição pública do snapshot autorizada em 2026-10-26. Todos os formatos
incluem LICENSE (GPL v3), LICENSE-DOCS (CC BY 4.0) e NOTICE (escopo/atribuição).
Os inventários são confrontados com os membros reais pela CI. Dependências
obtidas no destino conservam seus termos e não são incorporadas nestes pacotes.

| Formato | Textos e persistência |
|---|---|
| `.plasmoid` | LICENSE, LICENSE-DOCS e NOTICE na raiz do KPackage |
| `.pyz` | Textos na raiz, payload e widget; conservados no staging pelo instalador |
| Wheel | Três textos no diretório licenses de dist-info |
| Sdist | Três textos na raiz; wheel reconstruído conserva o mesmo inventário |

## Runtimes e imagens separados

| Formato | Bytes selecionados atualmente | Terceiros incorporados | Avisos aplicáveis | Ação pendente |
|---|---|---|---|---|
| Runtime instalado no destino | Pacotes resolvidos pelo pip e bindings do host | SDK, AWS CRT, cryptography, aiohttp e transitivas | Textos upstream das versões realmente obtidas; não inferir completude pela metadata | Inventário por plataforma e resolução; não redistribuir o venv com base no ZIP |
| Docker planejado | Backend + pip/setuptools conforme base + SDK/server + base Debian/CPython | Dependências Python, C/Rust/TLS, bibliotecas e ferramentas de sistema | LICENSE/NOTICE por pacote/subcomponente; termos PSF/Debian; fontes correspondentes quando exigidas | Base por digest, resolução/hashes, SBOM, fontes/patches/scripts e mecanismo de entrega comprovados |
| Docker histórico | Digest registrado em DOCKER_COMPLIANCE, produto 0.1.0 | Inventário histórico distinto do checkout 0.2.0 | Avisos de seus próprios bytes e fontes exatas | Decisão humana para tratamento da distribuição passada; build futuro não regulariza esse digest |

Para futura redistribuição de dependências, preparar cópias integrais e verificadas
dos textos pertinentes (sem substituir pelo nome SPDX): thinqconnect LICENSE;
awsiotsdk documents/LICENSE e NOTICE; awscrt LICENSE/NOTICE e seus subcomponentes;
aiohttp LICENSE.txt e vendor/llhttp/LICENSE; cryptography LICENSE e alternativa
selecionada, mais OpenSSL/Rust; MIT/BSD/PSF das transitivas. NOTICE é obrigação
condicionada ao conteúdo/termos aplicáveis, não um cabeçalho inventado.

Os avisos AWS v1.31.0 foram obtidos novamente e coincidem por SHA-256 com a auditoria
anterior. Isso sustenta a proposta técnica de conservar esses textos no payload que
incorporar o SDK; não prova correspondência integral do wheel nem resolve direitos
próprios. Ver [nativos](NATIVE_COMPONENTS.md), [dependências](DEPENDENCIES.md) e
[distribuição](DISTRIBUTION.md). Capturas preservadas fora do commit não pertencem
a esses payloads e precisam de revisão própria antes de qualquer publicação.

## Candidata gráfica H02–H04

Os quatro recursos gráficos e a composição de main.qml/FeatureCard.qml foram
substituídos na árvore de trabalho por [propostas neutras](ARTWORK.md). Os oito
fingerprints antigos conhecidos são recusados nos ZIPs. A autorização atual abrange os materiais próprios do snapshot.
Os originais estão fora do novo histórico público e dos novos pacotes;
preservações privadas não são distribuídas. Esta troca não regulariza a imagem Docker histórica.
