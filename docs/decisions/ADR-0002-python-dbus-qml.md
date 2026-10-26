# ADR-0002 — Serviço Python separado de QML via D-Bus de sessão

- **Estado:** aceita para PoC; arquitetura de produção pendente das provas de conceito.
- **Contexto:** chamadas de rede não devem bloquear a UI e o serviço precisa ser testável sem o Plasmoid.
- **Decisão:** processo Python independente, IPC pelo Session Bus, UI QML no Plasma 6.
- **Alternativas:** rede direta em QML; um processo Qt/C++ para tudo; subprocessos de comando por cada ação.
- **Consequências:** separação de responsabilidades e testes isolados; será necessário um contrato IPC versionado e tratamento de serviço indisponível.
- **Critério de validação:** PoC bidirecional na Fase 0 em contexto Plasma real.
