# ADR-0001 — Avaliar ThinQ Connect como rota operacional primária

- **Estado:** aceita provisoriamente; confirmar na Fase 1.
- **Contexto:** protocolo privado do app móvel pode mudar e a compatibilidade do aparelho ainda não foi demonstrada.
- **Decisão:** testar a API oficial ThinQ Connect via PAT e SDK antes de reproduzir protocolo privado.
- **Alternativas:** engenharia reversa imediata; integração local de terceiros; outro mecanismo suportado pela LG.
- **Consequências:** menor dependência do app móvel se a API funcionar; ainda existe dependência da nuvem e da disponibilidade/compatibilidade da LG.
- **Revisitar se:** modelo ou funções obrigatórias não forem expostos, após diagnóstico completo e evidências.
