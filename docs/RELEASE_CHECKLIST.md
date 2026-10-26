# Gates da candidata e da publicação

A preparação técnica do LG ThinQ AirCon Widget 1.0.0rc1 é verificada pela
[CI e viewers](TESTING.md): lint/format, unidade/contratos/QtTest, metadados,
documentação, catálogos, ativação sintética e builds exatos dos quatro formatos.
O resultado efetivo é registrado no relatório externo da execução.

Publicação deste snapshot autorizada em 2026-10-26, sob GPL-3.0-or-later para
código/recursos próprios e CC BY 4.0 para prosa própria. Para futuras entregas:

- Conservar origem e autorizações por caminho no [inventário](RIGHTS_INVENTORY.md).
- Verificar os textos completos e avisos selecionados em cada [payload](ARTIFACT_NOTICES.md).
- Revisar os terceiros realmente redistribuídos e fontes correspondentes quando exigidas.
- Declarar a cobertura ambiental efetiva e executar a [aceitação](OPERATIONAL_ACCEPTANCE.md).
- Declarar o estado linguístico: os POs são rascunhos sem traduções aprovadas.
- Conferir URLs e metadados públicos depois da publicação autorizada no novo repositório.
- Imagens, releases e Store permanecem entregas separadas desta publicação do código.

A imagem histórica mantém gate próprio de [conformidade Docker](DOCKER_COMPLIANCE.md).
Windows/GNOME não bloqueiam a candidata KDE. Os gates e ações mínimas estão
classificados em [V1_READINESS](V1_READINESS.md), sem reabrir auditoria geral.
