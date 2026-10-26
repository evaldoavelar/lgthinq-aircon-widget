# ADR-0004 — UI baseada em capacidades verificadas

- **Estado:** aceita.
- **Contexto:** capacidades variam entre modelos e firmwares; a API pode não expor todas as funções do aplicativo.
- **Decisão:** o serviço normaliza e publica capacidades reais; QML mostra somente controles confirmados e utiliza faixa/passo fornecidos pelo perfil quando disponíveis.
- **Alternativas:** hardcode de modos e temperatura; mostrar todos os controles e descobrir erro ao enviar.
- **Consequências:** UI mais fiel ao aparelho, com maior esforço de normalização e testes para perfis incompletos.
- **Regra:** dados ausentes não podem ser substituídos por valores fictícios na UI de produção.
