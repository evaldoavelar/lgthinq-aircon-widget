# Candidata V1 — LG ThinQ AirCon Widget 1.0.0rc1

Esta é a candidata local KDE Plasma 6, exclusiva para ar-condicionado LG ThinQ.
**Distribuição pública autorizada em 2026-10-26.** O relatório externo de entrega registra
os resultados efetivamente executados; este documento delimita critérios e gates.
`docs/STATUS.md` é contexto histórico local, não o estado público desta candidata.

## Escopo e evidência exigida

| Fluxo | Implementação / verificação |
|---|---|
| Instalar, atualizar e remover | `.pyz`, staging real até a chamada pip, rollback e KPackage isolado; pip/systemd do instalador interceptados nos testes |
| Ativar e recuperar | D-Bus privado com ativação sob demanda, crash e reativação; nenhuma unidade persistente do host alterada |
| Configurar e selecionar | Configuration1 e controlador local; cofre fake, seleção múltipla, persistência de ID, reinício e PAT transitório não retornado |
| Ler, atualizar e comandar | Snapshot/Refresh/Command com backend sintético; confirmação de estado, validação do perfil, prévia/coalescência e erros |
| Interface | Viewer sintético, painel/menu/configuração e popup baixo com rolagem; QtTest e qmllint |
| Empacotar | Inventários exatos de pyz/plasmoid/wheel/sdist, reconstrução de wheel, smokes sem dependências e provas negativas |
| Regressões | R03 nega controle; R04 persiste seleção; R07 encaminha Refresh remoto; R09 preserva inputs de build |

Não foram autorizados login LG nem controle físico nesta preparação. A aprovação
sintética confirma os contratos e comportamento testados, sem certificar aparelho,
rede LG ou cofre real. A API real permanece sujeita a conta, região, modelo e perfil.
UI não inventa capacidades; rede fica no backend assíncrono.

## Internacionalização

| Domínio | Mensagens por PO | Idiomas de trabalho | Revisão/tradução faltante |
|---|---:|---|---|
| Widget | 108 | en, pt_BR | 108 em cada idioma |
| CLI/instalador | 66 | en, pt_BR | 66 em cada idioma |

São 348 entradas idioma/mensagem por revisar, zero traduções aprovadas. Os quatro
MOs vazios são selecionados explicitamente e usam fallback. O texto-fonte é misto;
a revisão humana deve decidir a redação de referência. Extração UTF-8, contextos,
placeholders, plurais, compilação e carregamento são verificáveis separadamente
com traduções sintéticas que não integram o produto. Veja [I18N](I18N.md).

## Aceitação e pendências externas

| Classificação | O que falta / por que importa / ação mínima |
|---|---|
| Pendência jurídica de distribuição | Docker histórico tem questões próprias de nativos/avisos/fonte correspondente; responsável decide tratamento do digest; nova candidata não o regulariza |
| Pendência de tradução | Revisão dos 348 itens e autoria/permissão dos textos; infraestrutura pronta não equivale a idioma revisado |
| Pendência de validação ambiental | Instalação com resolução real de extras, cofre real com segredo sintético, novo login, temas/acessibilidade e Plasma 6.4; executar OP01–OP15 no ambiente escolhido |
| Pendência de validação ambiental | Autenticação LG, leitura e comandos físicos não exercitados nesta tarefa; exigem autorização e ensaio manual próprios |
| Validação da publicação | Conferir clone e instalação a partir do novo commit raiz; links locais e payloads são verificados pela CI |
| Melhoria futura fora do escopo | Windows, GNOME, builds byte a byte e matriz ampliada; não bloqueiam a preparação KDE |

Nenhum bloqueador técnico conhecido será tratado como resolvido sem teste. Falha
reproduzível deve ser corrigida antes de encerrar a candidata. Questões externas
acima não reabrem automaticamente a preparação técnica concluída.

## Fontes de orientação

[Instalação](INSTALL.md), [testes reproduzíveis](TESTING.md),
[arquitetura e compatibilidade de IDs](ARCHITECTURE.md), [distribuição](DISTRIBUTION.md),
[licenciamento](LICENSING.md), [inventário](RIGHTS_INVENTORY.md), [arte](ARTWORK.md)
e [aceitação ambiental](OPERATIONAL_ACCEPTANCE.md).

A autorização atual inclui publicação do snapshot e reescrita do histórico como
um único Initial Commit, com licenças dos materiais próprios aplicadas conforme
[LICENSING](LICENSING.md). Não inclui imagens Docker, releases ou Store.
