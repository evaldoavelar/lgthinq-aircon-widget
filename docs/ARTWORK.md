# Artes neutras — proposta para revisão H02–H04

Distribuição dos recursos próprios atuais autorizada em 2026-10-26 sob
GPL-3.0-or-later. A autorização do mantenedor não afirma autoria exclusiva nem
direitos sobre marcas de terceiros. Origem e processo observado seguem abaixo.

## Processo e limite da evidência

A receita abaixo foi registrada em brief textual externo antes da escrita. Codex
assistiu a criação de primitivas SVG/QML na proposta de 2026-10-24, sem importar paths de uma
biblioteca gráfica, traçar a imagem antiga ou reproduzir screenshots de terceiros.
Os recursos anteriores foram vistos para investigação e compatibilidade; portanto
não há alegação de clean room ou prova jurídica de criação independente/exclusiva.
O processo e os diffs são verificáveis; a autorização atual do responsável cobre somente os materiais próprios. Nenhum autor/ano de copyright/SPDX foi inventado.

[Proveniência gráfica estruturada](graphics-provenance.json): um registro por fonte,
receita, processo, hash atual, versões aposentadas, reutilização funcional e pendências.
O [inventário de direitos completo](RIGHTS_INVENTORY.md) mantém grupos de origem e
a autorização atual do mantenedor em cada caminho, sem certificar titularidade.

## Receita nova

| Fonte | Receita | Papel e dependência |
|---|---|---|
| lgthinq.svg | Grade24x24, cinco blocos5x4: (4,3),(4,10),(4,17),(15,6),(15,13); cor plana #526b9f, sem tile/gradiente/letra ou referência externa | Marca abstrata de dois fluxos de amostras; arquivo único para metadata/seletor |
| PanelIcon.qml | A mesma grade de cinco blocos; escala pelas dimensões, foreground ligado à paleta | Variante do próprio recurso novo; powered é propriedade herdada, não inventa status |
| AirConditioner.qml | Usa o PanelIcon novo, centralizado; cor pelo powered confirmado | Nome histórico preservado para chamadas; representa decoração abstrata, sem carcaça ou ThinQ; não representa medições |
| IconGlyph.qml | Mode: quatro quadrados; fan: três barras verticais; sleep: um ponto e duas linhas; eco: três pontos diagonais; power: quadrado e dois marcadores laterais; direction: três segmentos de comprimentos distintos | Chaves técnicas antigas preservadas, sem desenho de neve/pás/lua/folha/aparelho. Rótulos textuais e nomes acessíveis continuam necessários |
| main.qml | Formulário vertical de medidas/controles nativos e lista de características; marca pequena no cabeçalho | Composição nova; controlador/capacidades/IPC/menu herdados e ainda sob revisão de direitos; sem hero de aparelho ou grid de quatro cards |
| FeatureCard.qml | Linha horizontal com glifo, nome, valor e indicador textual | Propriedades/callbacks/i18n herdados; composição visual nova |

A arte abstrata não garante identificação intuitiva de cada função. Os rótulos e
acessibilidade preservam o significado; avaliação visual/de usabilidade é pendente.
Nenhum valor/capacidade de ar-condicionado novo foi fixado. QtQuick/Controls,
Kirigami e Plasma são dependências do host, com termos próprios; os arquivos deles
não entram nos ZIPs. Os menus ainda podem resolver nomes de ícones do tema em runtime.
Fontes tipográficas/símbolos de texto também são renderizados pelo sistema.

## Preservação, histórico e candidata

Oito versões distintas dos seis arquivos foram preservadas externamente, com hash,
antes da troca. O inventário por hash e os snapshots anteriores estão sob controle do responsável. Os originais não estão na candidata
de trabalho nem nos novos ZIPs. O histórico público foi recriado sem os originais; backups privados não são distribuídos. Não copiar preservações para assets/fixtures do projeto.

A investigação local confirmou Canvas/geometria embutidos sem crédito/fonte externa
comprovada. ADR-0009 registra KDE Connect como referência histórica do card/tema;
isso não prova cópia nem permissão. Não foi achada uma biblioteca de glifos que
comprovasse origem dos seis desenhos. Não se concluiu domínio público por serem
formas genéricas. A criação nova usa a receita acima, não essa referência.

`package_manifest.py` rejeita os oito fingerprints históricos em fontes selecionadas
e nos membros reais dos ZIPs, mesmo sob outro nome. Isso detecta bytes conhecidos;
qualquer alteração pode mudar o hash. Não é detector de cópia/derivação, auditoria
jurídica ou mecanismo contra uma alteração deliberada da política. A seleção exata
continua obrigatória, sem inclusão por glob de backups ou outros recursos.

## Revisão e manutenção

- Preservar os registros históricos de origem e os direitos de terceiros.
- Preservar a evidência de criação assistida dos seis arquivos e a autorização atual.
- ThinQ foi retirado da ilustração; nomes de compatibilidade não implicam endosso ou licença de marca (H04).
- Validar legibilidade em escalas/paletas, leitura dos glifos, foco/teclado e desktop composto.
- Testes QML, viewer e pacotes comprovam comportamento/conteúdo no ambiente observado; não concedem direitos.

Na candidata 1.0.0rc1, main.qml recebeu dois labels de identidade e mensagens
traduzíveis para erros/estados conhecidos, com fallback para categorias desconhecidas.
Receita e geometrias dos seis fontes permanecem as da proposta de 2026-10-24.
