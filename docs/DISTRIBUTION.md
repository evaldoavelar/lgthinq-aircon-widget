# Distribuição do LG ThinQ AirCon Widget

Distribuição pública do snapshot `1.0.0rc1` autorizada em 2026-10-26.
Materiais próprios seguem GPL-3.0-or-later (código/recursos) e CC BY 4.0 (prosa),
conforme [licenciamento](LICENSING.md). Aceitação ambiental continua pendente.

## Formatos técnicos preparados

| Formato | Conteúdo previsto | Uso |
|---|---|---|
| `.pyz` | 52 membros: instalador, helper gettext, manifesto e README; payload com pyproject/BACKEND/MANIFEST, 15 módulos, dois MOs Python e widget; dois MOs também na raiz para o instalador; licenças/NOTICE na raiz, payload e widget | install/update/remove/check no usuário; cria runtime e registra D-Bus/systemd sob demanda |
| `.plasmoid` | 19 arquivos: README autossuficiente, metadata, QML/XML/SVG e dois MOs de fallback | KPackage install/upgrade/remove; requer backend separado |
| Wheel técnico | 25 arquivos: 15 módulos, dois MOs Python e cinco metadados | Build/smoke local do backend; não é instalador do produto |
| Sdist técnico | 31 arquivos: fontes, dois MOs, BACKEND, pyproject, MANIFEST e metadata setuptools | Reconstrução offline do wheel com backend de build existente |

Nome da distribuição Python: `lgthinq-aircon-widget`. Módulo, CLI, cofre/configuração e nomes `.pyz`/`.plasmoid` são conservados.
Plasma/D-Bus adotam org.lgthinq; instalações antigas exigem reinstalação, conforme
[arquitetura](ARCHITECTURE.md). Não há migração de PAT ou seleção. Catálogos en/pt_BR
são rascunhos vazios: fallback para fontes mistas, sem tradução aprovada.

Os artefatos não incorporam SDK, venv, Qt ou bibliotecas de terceiros. Extras
declaram dependências; o instalador as obtém no destino. Isso não autoriza
redistribuir um runtime. Consulte [dependências](DEPENDENCIES.md) e
[avisos por payload](ARTIFACT_NOTICES.md).

## Construir e verificar localmente

Use cópia isolada do checkout público candidato e diretório novo. Não sobrescreva
artefatos anteriores. Os comandos de build não instalam nem publicam:

```sh
python3 scripts/build_local.py --output dist/review/lgthinq-local.pyz
python3 scripts/prepare_deploy.py --output dist/review --python "$PWD/.venv-runtime/bin/python" --config "$HOME/.config/lgthinq-kde/config.json"
python3 scripts/check_python_packages.py --output dist/python-review
sha256sum dist/review/lgthinq-local.pyz dist/review/lgthinq.plasmoid > dist/review/SHA256SUMS
sha256sum --check dist/review/SHA256SUMS
```

O build Python exige setuptools, wheel e pip já disponíveis; pode usar
`LGTHINQ_BUILD_PYTHON` para um ambiente existente. Não baixa ferramentas durante a
CI. O checker verifica inventário completo, reconstrói wheel e faz smoke instalado
sem dependências em destino isolado. Timestamps e resolução futura de dependências
não são fixos; não se promete reprodução byte a byte.

[TESTING](TESTING.md) descreve a rodada única de CI e viewers. São exercitados
inventários, symlinks, duplicatas, tipos especiais, payload extra/privado, ausência
de arquivos obrigatórios, links/âncoras e fingerprint de arte aposentada. Sentinelas
são sintéticas. O manifesto é por caminhos exatos; novos recursos/MOs/avisos
exigem seleção explícita. Nem Git tracking nem extensão de arquivo autorizam inclusão.

## Instalar, atualizar e remover

A [instalação integrada](INSTALL.md) é a rota KDE. A `.pyz` baixa os extras,
valida o runtime antes de alterar registros, preserva rollback e configura
ativação D-Bus. Atualização conserva o ID do Plasmoid, configuração e cofre.
Remoção preserva credencial/configuração e remove apenas instalação gerenciada.
O [deploy manual](DEPLOY.md) é uma alternativa avançada. O `.plasmoid` sozinho
não instala Python nem registra backend.

Testes de pip/venv/systemd são interceptados; KPackage e ativação D-Bus usam
ambientes temporários. Download real de extras, cofre, novo login e uso físico
continuam como [validação ambiental](OPERATIONAL_ACCEPTANCE.md).

## Licenças e distribuição

LICENSE, LICENSE-DOCS e NOTICE estão selecionados explicitamente em cada formato.
O instalador conserva esses arquivos no staging e no runtime; wheel e sdist
incluem os mesmos textos. Os [registros por caminho](RIGHTS_INVENTORY.md) mantêm
origem observada e autorização do mantenedor sem certificar titularidade alheia.

Internos locais e recursos aposentados estão fora do novo commit raiz público.
Não envie backups do histórico anterior. A imagem [Docker histórica](DOCKER_COMPLIANCE.md)
conserva gate próprio fechado; não há push, retag ou publicação de imagem nesta
operação. Store e releases não são produzidos pelo envio do repositório.
