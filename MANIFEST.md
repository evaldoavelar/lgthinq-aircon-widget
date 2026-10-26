# Mapa do projeto

| Caminho | Finalidade |
|---|---|
| `src/lgthinq_daemon/` | Backend, configuração, cofre, SDK, HTTP e D-Bus |
| `plasmoid/` | Metadados, QML, configuração e SVG do widget |
| `packaging/` | Templates systemd e opção Docker |
| `scripts/` | Build, instalação, diagnóstico e verificações |
| `tests/` | Fixtures sintéticas, unidade, contratos, QtTest e integração |
| `poc/phase-0-dbus/` | Demonstração de IPC, separada da UI de produção |
| `docs/` | Guias públicos, contratos, requisitos e decisões de engenharia |
| `pyproject.toml` | Versão, extras Python e configuração de ferramentas |

Os inventários exatos de `.pyz` e `.plasmoid` estão em
`scripts/package_manifest.py`; novos arquivos exigem inclusão explícita e regressão.
Rastreamento Git e extensões não autorizam inclusão. Veja
[distribuição](docs/DISTRIBUTION.md) e [direitos](docs/RIGHTS_INVENTORY.md).
Ambientes virtuais, caches, logs e produtos de build são locais e ficam fora dos
artefatos de distribuição. Relatórios privados e instruções de agentes não fazem
parte das fontes do produto.

A revisão de distribuição inclui [direitos por caminho](docs/rights-provenance.json),
[avisos por payload](docs/ARTIFACT_NOTICES.md), [componentes nativos](docs/NATIVE_COMPONENTS.md)
e [aceitação operacional](docs/OPERATIONAL_ACCEPTANCE.md).
`scripts/audit_distribution.py` inventaria evidências sem rede/execução de dependências
e verifica a cobertura de direitos na CI; não concede autorização de distribuição.
