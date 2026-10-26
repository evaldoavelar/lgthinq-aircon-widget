# Checklist operacional — LG ThinQ AirCon Widget 1.0.0rc1

Preparado em 2026-10-25 para validação manual da candidata existente em VM ou
usuário de teste. A candidata está tecnicamente encerrada conforme informado pelo
responsável. Este checklist não reabre auditoria nem repete a CI. **Nenhum ensaio
operacional foi executado nesta tarefa.**

## Limites de uso

- Usar exclusivamente os artefatos da entrega `1.0.0rc1`, sem reconstrução.
- Executar ensaios somente em ambiente de teste designado. Os procedimentos abaixo
  são instruções para execução futura, não autorização para instalar agora.
- Preservar os 25 arquivos internos, evidências, backups, artefatos e alterações
  existentes. Não levar o checkout privado inteiro para a VM.
- Não alterar `docs/STATUS.md`, código, remotes ou histórico; não fazer commit,
  push, publicação, Docker/homelab, instalação global ou operação destrutiva.
- Não usar `sudo`. Se faltar ferramenta ou pré-requisito, registrar **Não
  executado** e o motivo; não instalar ferramentas como parte deste checklist.
- Testes locais usam conta limpa, sem PAT, sem configuração LG anterior e sem
  acesso à LG. Rede para dependências Python é separada da rede LG; se não puder
  manter essa separação, não prosseguir com a instalação.
- Cofre real exige autorização própria, mesmo com segredo sintético. Autenticação
  e leitura LG exigem autorização específica; controle físico exige autorização
  adicional da ação e presença do operador. Nenhuma dessas autorizações foi dada.
- Defeito reproduzível: registrar a ficha ao final e aguardar decisão do usuário
  antes de corrigir código. Não reconstruir a candidata para contornar a falha.

## Identificação obrigatória da execução

Preencher antes do primeiro teste; não reutilizar resultados de outra VM/sessão.

| Campo | Registro |
|---|---|
| Operador, data/hora e fuso; autorização aplicável | A preencher |
| VM/usuário de teste (alias sanitizado), imagem/snapshot de origem | A preencher |
| Distribuição e versão; arquitetura | A preencher |
| Plasma, Qt, Python, systemd e KPackage; ferramentas ausentes | A preencher |
| Wayland/X11; resolução; escala; tema; contraste | A preencher |
| Locale/LANGUAGE e tecnologia assistiva, quando usada | A preencher |
| Instalação anterior, configuração e credenciais | Confirmar ausência no perfil limpo; descrever apenas dados sintéticos em perfil de atualização |
| Conectividade | Sem LG; indicar se há acesso apenas ao índice de dependências |
| Backend/versão do cofre e estado bloqueado/desbloqueado | A preencher apenas nos ensaios autorizados de cofre |
| Diretório exclusivo das evidências no ambiente de teste | A preencher; não sobrescrever evidência anterior |

Comandos de identificação, executados **na VM/conta de teste** e registrados com
seus códigos de saída: `cat /etc/os-release`, `uname -m`, `python3 --version`,
`plasmashell --version`, `qtpaths6 --qt-version`, `kpackagetool6 --version`,
`systemctl --version`. Registrar compositor/escala/tema pela configuração da sessão.
Se `qtpaths6` não existir, registrar a versão Qt pela ferramenta já disponível,
identificando a fonte; não instalar uma ferramenta para completar a ficha.

O host onde este documento foi preparado é Arch Linux rolling, x86_64. Isso não é
o ambiente de aceitação; Plasma/Qt/Python desse host não foram ensaiados aqui.

## Artefatos: versão e hashes

Nesta preparação, `dist/` estava vazio. O relatório final externo e seus checksums
não estavam disponíveis nos documentos consultados. **Não há SHA-256 aferido dos
pacotes nesta tarefa.** Obter os arquivos já produzidos e a referência de hashes da
entrega encerrada; não gerar substitutos. Ausência/divergência bloqueia os testes
dependentes, sem reabrir a auditoria.

| Artefato existente | Versão esperada | SHA-256 da entrega | SHA-256 da cópia de teste | Situação inicial |
|---|---|---|---|---|
| `lgthinq-local.pyz` (rota integrada) | `1.0.0rc1` | Não disponível | Não aferido | Não executado — arquivo ausente neste workspace |
| `lgthinq.plasmoid` (rota manual alternativa) | `1.0.0rc1` | Não disponível | Não aferido | Não executado — arquivo ausente neste workspace |
| Wheel técnico, se incluído na entrega | `1.0.0rc1` | Não disponível | Não aferido | Não executado — não necessário à rota integrada |
| Sdist técnico, se incluído na entrega | `1.0.0rc1` | Não disponível | Não aferido | Não executado — não reconstruir |

Registrar nome exato, tamanho, origem lógica e versão de cada arquivo recebido.
Na pasta dos artefatos existentes, usar `sha256sum ./lgthinq-local.pyz` e,
se recebido, `sha256sum ./lgthinq.plasmoid`; comparar com os hashes da entrega.
Repetir a leitura de hash após o ensaio e preservar os dois registros.
Para wheel/sdist recebidos, usar seus nomes exatos no mesmo comando, sem instalar
ou reconstruir apenas para preencher esta tabela. Hash calculado apenas no destino
identifica os bytes recebidos, mas não comprova correspondência com a entrega.

## A — Testes locais, sem cofre real, conta LG ou aparelho

Aplicar em sequência na rota integrada, com artefatos verificados. Para cada linha,
preencher também a ficha de execução. Ausência de pré-requisito é **Não executado**;
falha observada do produto em condições válidas é **Reprovado**.

| ID / teste | Procedimento | Resultado esperado | Critério objetivo de aprovação | Classificação inicial e motivo |
|---|---|---|---|---|
| L01 — Identidade dos artefatos | Preencher ambiente e tabela acima; comparar SHA-256 de origem e destino e versão da metadata embutida, por leitura do pacote existente. Não executar builders/checkers. | Mesma candidata da entrega. | Hashes idênticos para todos os artefatos usados; versão `1.0.0rc1`; origem registrada. | **Não executado** — artefatos/checksums não disponíveis. |
| L02 — Pré-requisitos | No perfil limpo, executar `python3 ./lgthinq-local.pyz check` e `python3 ./lgthinq-local.pyz --help`. | Diagnóstico e ajuda utilizáveis, sem cadastrar credencial ou instalar componentes. | Código 0 e pré-requisitos satisfeitos para prosseguir; registrar diagnóstico se faltarem componentes. | **Não executado** — depende de L01 e ambiente designado. |
| L03 — Instalação integrada | Com execução futura autorizada no usuário de teste, executar `python3 ./lgthinq-local.pyz install`; listar `kpackagetool6 --type Plasma/Applet --list`; adicionar o widget. Não preencher PAT. Registrar versões das dependências efetivamente resolvidas. | Runtime do usuário, widget e registros D-Bus/systemd criados; nenhuma solicitação de login LG. | Exit 0; ID `org.lgthinq.aircon` presente; widget abre; instalação restrita ao usuário, sem controle habilitado. | **Não executado** — depende de L01/L02 e autorização de instalação no teste. |
| L04 — Primeiro uso sem credencial | Abrir popup e configurações; não usar Salvar e conectar nem Buscar aparelhos. Consultar `systemctl --user show lgthinq-local.service -p ActiveState -p SubState -p NRestarts`. | Backend ativa sob demanda; configuração acessível; indicação de configuração necessária; nenhuma temperatura/capacidade real inventada. | Configuração abre sem travar; serviço não entra em reinício contínuo; nenhum dado de aparelho é apresentado como real. | **Não executado** — depende de L03. |
| L05 — Novo login | Sair e entrar somente na sessão de teste; abrir o widget e repetir L04. Não habilitar a unidade com `enable`. | Ativação funciona após novo login sem terminal permanente. | Widget/configuração abrem e backend ativa sem intervenção nem ciclos de reinício. | **Não executado** — depende de L03 e sessão de teste. |
| L06 — Fluxo sintético | Na sessão privada descrita abaixo, abrir o widget instalado; atualizar; editar temperatura com passos rápidos; testar controles disponíveis. | Dados sintéticos, edição com prévia e posterior estado confirmado; UI responsiva. | Snapshot identificado como simulado; Atualizar termina; valor final permitido é confirmado; indicador não antecipa confirmação. Registrar valor/horários sintéticos. Quantidade de comandos só é aprovada se houver evidência sintética que a demonstre. | **Não executado** — depende de L03 e viewer já disponível. |
| L07 — Composição visual | Na mesma simulação, testar painel horizontal/vertical e popup em área baixa; Breeze claro/escuro e escalas 100/125/150/200% disponíveis. Registrar cada combinação separadamente. | Texto, rolagem, menus e controles legíveis e alcançáveis. | Sem recortes que impeçam ação/leitura; popup fecha corretamente; captura sintética por combinação. Uma combinação não aprova as demais. | **Não executado** — depende de L06 e recursos do ambiente. |
| L08 — Teclado/acessibilidade | Na simulação, percorrer Tab/Shift-Tab, setas, Enter e Escape; usar leitor de tela se já disponível. | Foco visível, sequência lógica, ações nomeadas e limites respeitados. | Cada ação disponível alcançável e acionável; Escape fecha; nomes e estados anunciados quando houver leitor. Parte não coberta fica Não executado. | **Não executado** — depende de L06 e tecnologia assistiva disponível. |
| L09 — Idiomas/fallback | Abrir viewers separados com `LANGUAGE=pt_BR` e `LANGUAGE=en`, restritos ao processo; observar popup/configuração. Não editar nem substituir catálogos. | Fallback atual para fontes mistas; não há tradução aprovada nesta candidata. | Sem mensagens vazias, placeholders literais/quebrados ou ações inacessíveis por texto. Registrar telas; não declarar tradução completa aprovada. | **Não executado** — depende de L06. |
| L10 — Indisponibilidade e recuperação | No bus privado, encerrar somente o backend sintético pelo Ctrl+C; observar widget; reiniciar o mesmo comando sintético. | Indicação de indisponibilidade e recuperação sem derrubar a interface. | Erro visível ao perder serviço; estado sintético volta após reinício; UI continua respondendo. Registrar tempos observados. | **Não executado** — depende de L06. |
| L11 — Reaplicar a mesma candidata | Em perfil de teste instalado, guardar cópia de configuração não secreta e registrar opções de aparência; executar `python3 ./lgthinq-local.pyz update` com o mesmo hash; reabrir widget. | Reinstalação gerenciada preserva opções. | Exit 0; mesma versão/ID; opções preservadas; L04 continua funcionando. Não certifica migração entre versões nem preservação de PAT real. | **Não executado** — depende de L03 e autorização futura de atualização no teste. |

Para L06–L10, usar **o backend e o widget instalados pelo pacote existente**,
sem `PYTHONPATH=src`, checkout ou suíte de CI. Na conta limpa, sem configuração LG,
abrir um shell com bus privado: `dbus-run-session -- bash --noprofile --norc`.
Nesse shell, iniciar somente estes processos de teste:

```sh
"${XDG_DATA_HOME:-$HOME/.local/share}/lgthinq-local/current/venv/bin/python" -m lgthinq_daemon --simulate serve &
RC1_SIM_PID=$!
plasmoidviewer -a org.lgthinq.aircon &
RC1_VIEWER_PID=$!
```

Para L10, encerrar exclusivamente esse backend sintético com
`kill -TERM "$RC1_SIM_PID"`, seguido de `wait "$RC1_SIM_PID"`; manter o viewer
aberto, observar o erro e repetir o comando do backend, atualizando `RC1_SIM_PID`.
Não encerrar o serviço da sessão normal. Se o viewer ativar outro backend ou não
resolver o pacote instalado, registrar **Não executado** por isolamento insuficiente;
não adaptar código ou unidades para prosseguir. Ao terminar, fechar o viewer pela
janela, encerrar somente o backend de teste ainda em execução pelo PID registrado,
aguardar sua saída e fechar o shell privado. Não reutilizar PIDs de sessões antigas.
Composição no painel real exige um ensaio separado
nesse ambiente de teste; o viewer sozinho não a certifica.

## B — Cofre real, somente com segredo sintético e autorização própria

Usar usuário/cofre descartável dedicado e rede LG indisponível. Não usar a ação
Salvar e conectar com um segredo sintético: esse fluxo também inicia descoberta LG.
Executar com o Python do runtime instalado e `-m lgthinq_daemon` (caminho de L06).

| ID / teste | Procedimento | Resultado esperado | Critério objetivo de aprovação | Classificação inicial e motivo |
|---|---|---|---|---|
| V01 — Gravar e recuperar | Após autorização, usar `--account rc1-synthetic-op credential-set`, fornecendo segredo sintético apenas na entrada oculta. Pelo adaptador `Vault` instalado, ler esse alias e comparar em memória, emitindo somente igualdade booleana; não exibir o retorno. Repetir em sessões separadas para Secret Service e KWallet disponíveis, identificando o backend efetivo. | Segredo guardado no backend seguro, recuperável pelo adaptador. | Gravação exit 0, comparação verdadeira, backend identificado; nenhum segredo em argumentos/configuração/logs. Resultado separado por backend. | **Não executado** — cofre real não autorizado; precisa de ambiente dedicado. |
| V02 — Negação e recuperação | No cofre dedicado, bloquear/negar desbloqueio e repetir armazenamento do segredo sintético; depois desbloquear e repetir V01. Se o backend cancelar em vez de bloquear, registrar o cenário exato. | Erro explícito ao negar acesso, sem fallback; recuperação após desbloqueio. | Falha categorizada durante negação; nenhum arquivo de credencial alternativo criado; V01 passa após desbloqueio. | **Não executado** — depende de autorização e V01. |

Esses ensaios não aprovam autenticação LG nem o fluxo integrado Configure. Se não
houver meio existente de observar backend/igualdade sem revelar o segredo, deixar
a parte correspondente **Não executado**, sem criar ferramenta ou alterar código.

## C — Autenticação e leitura LG: autorização específica pendente

| ID / teste | Procedimento após autorização | Resultado esperado | Critério objetivo de aprovação | Classificação inicial e motivo |
|---|---|---|---|---|
| G01 — Conectar em somente leitura | Operador insere PAT somente no campo oculto e país correto, mantém Permitir comandos desmarcado e usa Salvar e conectar. Nunca pedir senha LG. | Autenticação/discovery e credencial no cofre; campo limpo após submissão. | Conexão concluída; opções não secretas com controle desabilitado; segredo ausente de config e evidência sanitizada. | **Não executado** — sem autorização de conta LG/credencial real; depende de cofre validado. |
| G02 — Seleção e leitura | Com G01, selecionar manualmente o AC autorizado; abrir popup, atualizar e comparar leitura/unidade com observação do operador. Reabrir a sessão e confirmar seleção. | Aparelho correto, ID persistente, capacidades coerentes com perfil, ausência de dados tratada sem fabricar valor. | Seleção preservada; leituras/unidades correspondem às observações registradas dentro do intervalo de atualização medido; controles reais permanecem indisponíveis. | **Não executado** — depende de G01 e aparelho autorizado para leitura. |
| G03 — Rede/autenticação e reconexão | Após autorização do cenário, interromper apenas a rede da VM e restaurar; erro de PAT expirado/revogado somente em credencial de teste já disponível ou com autorização específica para revogá-la. | Erro sanitizado, UI responsiva, backoff; autenticação requer intervenção em vez de retry agressivo. | Categoria correta, sem falso estado conectado/sucesso, sem segredo exposto; recuperação após rede/credencial restabelecida. Registrar tentativas/tempos; não provocar limites de taxa da LG. | **Não executado** — depende de G01 e autorização dos cenários. |

## D — Controle físico: autorização adicional pendente

| ID / teste | Procedimento após autorização | Resultado esperado | Critério objetivo de aprovação | Classificação inicial e motivo |
|---|---|---|---|---|
| F01 — Uma ação física aprovada | Operador presente registra aparelho por alias, ação/valor permitido pelo perfil e estado inicial; habilita comandos e executa uma única ação aprovada; observa confirmação e aparelho. Não repetir automaticamente em timeout. | Uma ação física correspondente; estado confirmado após leitura; falha não aparece como sucesso. | Resultado físico e estado confirmado concordam, sem ação adicional; em timeout o resultado fica indeterminado até verificação manual e o teste não é aprovado. | **Não executado** — controle físico não autorizado; depende de G01/G02. |
| F02 — Encerramento físico | Operador restaura o estado inicial pelo meio previamente aprovado, desabilita comandos e confere o estado final. | Aparelho no estado combinado; widget retorna a somente leitura. | Estado final observado e controle desabilitado registrados, sem novo comando após desabilitação. | **Não executado** — depende de autorização e F01. |

## E — Ensaios de ciclo de vida reservados

Não executar remoção, restauração de snapshot ou injeção de falha nesta tarefa.
Dependem de autorização futura específica em VM descartável; preservar a candidata
e suas evidências fora do alvo de qualquer restauração.

| ID / teste | Procedimento após autorização | Resultado esperado | Critério objetivo de aprovação | Classificação inicial e motivo |
|---|---|---|---|---|
| R01 — Falha de atualização/recuperação | Em clone descartável com a candidata instalada e snapshot, cortar somente acesso ao índice de dependências e executar update com o mesmo `.pyz`; registrar a etapa que falhou; restabelecer rede e verificar instalação anterior. Se cache impedir falha, não forçar alterações de código. | Falha explícita e instalação anterior preservada/recuperável. | Falha efetivamente ocorrida, configuração sintética preservada e L04 funcionando com runtime anterior; sem falha provocada, cenário Não executado. | **Não executado** — injeção/recuperação não autorizadas; VM ainda não designada. |
| R02 — Remoção gerenciada | No perfil descartável, retirar instância do painel; executar `python3 ./lgthinq-local.pyz remove`; consultar KPackage e unidade, comparando com inventário local prévio. | Apenas instalação gerenciada removida; configuração e eventual entrada sintética de cofre preservadas. | Exit 0; pacote/unidade/ativação gerenciados ausentes e nenhum processo gerenciado residual; arquivos alheios e configuração preservados. Não apagar configuração/cofre para completar o teste. | **Não executado** — remoção não autorizada nesta tarefa. |

## Registro de resultados e evidências

Uma ficha por teste e por combinação de ambiente. Usar apenas **Aprovado**,
**Reprovado** ou **Não executado**. Não transportar aprovação da CI encerrada para
estas fichas. Etapa parcialmente executada mantém resultado parcial descrito e
não recebe aprovação integral; separar a parte não executada e explicar o motivo.

```text
Teste / ambiente / operador / data-hora-fuso:
Autorização e pré-requisitos confirmados:
Artefatos, versões e SHA-256:
Procedimento efetivamente executado e códigos de saída:
Resultado esperado / critério objetivo:
Resultado observado (sanitizado):
Classificação: Aprovado | Reprovado | Não executado
Motivo da classificação / limitação:
Evidência sanitizada: nome lógico, horário, SHA-256
Estado final do ambiente / próximo passo:
```

Preservar capturas sintéticas e registros de versões, códigos, categorias de erro,
horários e conclusões. Revisar antes de salvar/compartilhar: não capturar PAT, senha,
cookies, Authorization, IDs/aliases reais, dumps D-Bus, JSON LG bruto ou journal
integral. Não exportar cofre. Credenciais não entram em comandos, arquivos ou
conversas. Preferir registrar a observação sanitizada em vez de guardar log bruto.
Calcular SHA-256 das evidências já sanitizadas e guardar junto ao registro; não
sobrescrever originais/evidências existentes nem adicioná-las ao Git nesta tarefa.

Ficha adicional obrigatória se houver defeito reproduzível:

```text
Defeito / teste / severidade observada:
Ambiente e hashes da candidata:
Pré-condições e autorização do cenário:
Passos mínimos numerados para reproduzir:
Resultado esperado e critério violado:
Resultado observado e frequência (ocorrências/tentativas):
Evidência sanitizada e SHA-256:
Impacto / estado final / testes dependentes não executados:
Decisão: aguardar o usuário; nenhuma correção aplicada.
```

Ao encerrar a execução futura, conferir hashes dos pacotes novamente, consolidar
contagens por classificação e listar os testes não executados com seus motivos.
Ausência de autorização/artefato não é aprovação nem defeito reproduzível.
Aceitação local, cofre, LG e física têm resultados separados; não concedem
autorização para distribuição/publicação.

## Entrega deste checklist

- Único arquivo criado: `docs/RC1_OPERATIONAL_CHECKLIST.md`.
- Testes, CI, builds, instalação, cofre, LG e controle físico: não executados.
- Versão-alvo registrada; hashes dos pacotes pendentes por ausência dos artefatos.
- Checklist com procedimentos, expectativas, critérios e classificação inicial:
  preparado. Aceitação operacional da candidata: não executada.
- `docs/STATUS.md` não atualizado. Nenhuma correção, commit ou publicação.

Referências de procedimento: [instalação integrada](packaging/LOCAL-INSTALL.md),
[arquitetura](ARCHITECTURE.md), [contrato D-Bus](DBUS_CONTRACT.md),
[segurança](SECURITY.md), [candidata V1](V1_READINESS.md) e
[aceitação operacional preexistente](OPERATIONAL_ACCEPTANCE.md).
Os comandos de CI/build presentes em outros guias não integram este checklist.
