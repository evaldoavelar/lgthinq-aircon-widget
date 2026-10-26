# LG ThinQ AirCon Widget — pacote Python técnico interno

Wheel e sdist contêm o backend 1.0.0rc1; não são um instalador do produto KDE.
Distribuição pública autorizada pelo mantenedor em 2026-10-26.
Código, exemplos executáveis, testes, configuração, catálogos e recursos SVG/QML
próprios: GPL-3.0-or-later. Prosa própria: CC BY 4.0, com atribuição a
LG ThinQ AirCon Widget contributors. Textos completos em LICENSE e LICENSE-DOCS;
NOTICE delimita o escopo. Direitos e avisos de terceiros permanecem próprios.

O wheel contém os 15 módulos lgthinq_daemon e metadata/entry point `lgthinq`.
O sdist contém as mesmas fontes, BACKEND.md, pyproject.toml, MANIFEST.in e metadata
gerada pelo setuptools. Nenhum deles inclui UI, scripts de instalação/CI, testes,
documentação completa. Incluem somente os dois catálogos Python de fallback
en/pt_BR; nenhuma tradução foi aprovada.
Os extras declaram dependências; não as incorporam. A instalação isolada não fornece
o widget, unidades systemd ou ativação D-Bus.

Smoke sem dependências ou credenciais: `python -m lgthinq_daemon --help` e
`python -m lgthinq_daemon --simulate status`. Python 3.11+ é necessário. Operação
real exige dependências opcionais e, no desktop, bindings D-Bus/GLib do sistema e
cofre suportado. O planejamento e a validação do produto exigem o checkout completo
revisado; este pacote não promete um procedimento operacional autossuficiente.

Instalação e smoke locais não encerram os gates de licença, Docker, extras reais,
cofre, novo login, Plasma ou aparelho. A publicação deste snapshot foi autorizada.

Nome da distribuição: `lgthinq-aircon-widget`. Módulo, CLI e domínios gettext
do backend são conservados. D-Bus e Plasma usam o namespace org.lgthinq.
