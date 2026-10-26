# ADR-0009 — Seleção de temperatura e superfície do popup

Status: adotada, 2026-10-22.

## Temperatura

Os botões enviavam cada passo imediatamente e dependiam da leitura LG antes do próximo
ajuste. Adotamos TemperatureEditor.qml, com prévia local independente do snapshot e
Timer de 700 ms reiniciado a cada mudança. Seis cliques de 0,5 °C podem selecionar
22 → 25 °C com um único comando. O arraste atualiza o número e só inicia a espera ao
soltar. Limites e passo vêm da capacidade, sem valores específicos de aparelho.

Fila limitada a uma intenção local: durante comando/polling, o último ajuste substitui
a seleção anterior e aguarda o backend livre. Não há threads bloqueadas, sleep, rede
QML, fila de passos intermediários ou repetição automática de comandos que falharam.
Voltar à temperatura já confirmada evita envio. Mudança de unidade/capacidade, perda
de permissão, erro ou desconexão cancela a prévia pendente. Comando já enviado não pode
ser cancelado fisicamente por essa ação.

A aceitação D-Bus não confirma o resultado. Só snapshot conectado com updated_at
posterior à submissão encerra a espera; o valor efetivamente lido prevalece, mesmo se
diferente do pedido. Snapshot antigo não encerra a espera. Edição adicional durante
comando pode prosseguir após a resposta, preservando apenas a última intenção.
A seleção é identificada como pendente; painel e snapshot continuam mostrando estado
confirmado. Esse comportamento não garante aplicação física ou consistência instantânea
da nuvem LG. Testes não enviam comando ao aparelho.

## Ícone e fundo

O ícone compacto passa a PanelIcon.qml, desenhado com primitivas QML em vez de lookup
no tema/imagem. Plasmoid.icon é QString: o arquivo local passa como caminho absoluto,
sem esquema file://, preservando o SVG para metadados/seletor de widgets. A captura do
compacto e o teste de pixels verificam conteúdo desenhado, não somente Image.Ready.

No host Plasma 6.8, CompactApplet.qml cria AppletPopup com StandardBackground/SolidBackground
independentemente de Plasmoid.backgroundHints. PlasmaWindow não oferece NoBackground;
o hint no applet só elimina fundo no contexto que o respeita. Trocar todo o diálogo
sacrificaria integração nativa. Para este host, procuramos o FrameSvg de dialogs/background
somente na árvore da própria janela do popup e vinculamos opacity=0. Binding restaura
o valor anterior ao ser destruído. Nenhum arquivo/configuração global é alterado.

**Limitação deliberada:** a árvore DialogBackground é implementação interna. O acesso
é guardado; se a estrutura mudar, o popup continua funcionando com fundo padrão e
precisará de nova validação visual. Atualizações de Plasma exigem repetir o harness.
Sombras/blur do compositor permanecem sob controle do Plasma; a personalização não é
um tema global. Teste nativo confirma frame encontrado/opacity=0. Captura direta do
contentItem da janela não funciona neste host (sem QQmlEngine); capturas preservadas
são do cartão e compacto, não do desktop ou da janela inteira.

Fontes primárias verificadas: código instalado de CompactApplet.qml, headers
PlasmaQuick/plasmawindow.h e metadata QML do host;
[PlasmaWindow](https://github.com/KDE/libplasma/blob/master/src/plasmaquick/plasmawindow.cpp),
[DialogBackground](https://github.com/KDE/libplasma/blob/master/src/plasmaquick/dialogbackground_p.h)
e [Slider Qt](https://doc.qt.io/qt-6/qml-qtquick-controls-slider.html).

## Revisão 0.1.5 — 2026-10-23

A captura do usuário demonstra fundo externo claro mesmo após a tentativa por opacity.
A causa exata na sessão não foi comprovada. O código PlasmaWindow confirma que os
hints disponíveis mantêm fundo e efeitos de compositor; esconder o SVG é insuficiente
como garantia de transparência. Substituímos a técnica interna por PlasmaCore.Dialog
com NoBackground, visualParent no compacto, localização do applet e fechamento ao
perder foco. O popup possui estado próprio para não abrir o AppletPopup temático.
A representação completa permanece para uso no desktop. Nenhum tema global é alterado.

PanelIcon usa traços monocromáticos e Kirigami.Theme.textColor herdada do painel,
incluindo mudanças de tema em runtime. O SVG colorido permanece apenas no catálogo.
A confirmação do resultado no plasmashell instalado continua sendo uma etapa manual.

## Revisão 0.1.7 — 2026-10-23

Pedido do usuário: usar o mesmo fundo do tema ativo do KDE, com KDE Connect como
referência. O card substitui o preto fixo por Kirigami.Theme.backgroundColor no
colorSet Window, sem herdar o conjunto de cores do painel. O binding acompanha
mudanças da paleta em runtime. A borda usa textColor com alfa 0,15; textos e ícones
sobre o fundo usam as cores semânticas do tema para preservar contraste. O diálogo
NoBackground e o contorno arredondado permanecem; controles internos preservam
as cores existentes. Não se fixa o hexadecimal observado na captura, pois ele
representa apenas um tema. Conferência no plasmashell instalado permanece manual.

## Revisão 0.1.8 — 2026-10-23

O usuário confirmou o fundo temático e relatou componentes muito escuros. Cartões,
botões, Eco e trilho do slider substituem os tons verdes fixos por mistura da cor
de janela com 10% da cor de texto. Isso clareia superfícies no tema escuro e escurece
no claro. Bordas usam texto a 20%; hover/pressionado dos cartões usam 15%/20%.
Textos e ícones seguem a paleta; energia ligada, Eco ativo e preenchimento do slider
usam destaque do KDE. Layout, capacidades e comportamento dos comandos preservados.

## Proposta visual de 2026-10-24 — H02–H04

As referências visuais históricas acima foram preservadas como evidência, não
como autorização de redistribuição. A candidata usa formulário/controles nativos
e decoração abstrata conforme [ARTWORK](../ARTWORK.md), em lugar da composição
com aparelho/cards. Seleção, confirmação, transporte e menu permanecem com seus
contratos. Testes/preview são técnicos, sem aprovação de direitos ou marca.
