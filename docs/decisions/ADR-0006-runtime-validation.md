# ADR-0006 — Validar IPC no viewer e preservar controles

- Estado: implementado e validado com backend simulado, 2026-10-22.
- Contexto: com acesso liberado, D-Bus e downloads funcionaram. O viewer expôs falhas
  de captura de log e ciclos de layout que a análise estática não demonstrava.
- Decisão: manter módulo nativo workspace.dbus, sem ponte C++ ou QProcess. Testar
  numa cópia temporária com instrumentação dos handlers reais de controles, snapshots,
  perda e recuperação do serviço. Registrar que isso não é clique físico nem LG real.
- UI: manter o modelo de chaves até mudança efetiva das capacidades, para não recriar
  controles a cada resposta. Flickable com largura independente do conteúdo e dimensões
  implícitas explícitas evitam ciclos de layout verificados no host.
- Runtime: GLibUnix.signal_add substitui a API GLib descontinuada na versão instalada.
  Revalidar bindings ao portar a outro sistema.
- Dependências: extras instalados em venv com bindings do sistema, sem mudar Python
  global. SDK confirmado por import/assinaturas, sem usar credenciais.
- Validação: harness `scripts/validate_phase0.py` com backend e bus isolados.
  Logs históricos ficam fora das fontes do produto; repetir conforme TESTING.md.
  Validação do aparelho e avaliação humana do painel permanecem pendentes.
