# ADR-0010 — Produto local integrado como caminho principal

- Estado: implementação autorizada e entregue; aceitação operacional real pendente.
- Data: 2026-10-23.
- Contexto: usuário quer instalar o widget, cadastrar PAT nas configurações e usar,
  sem administrar servidor. Escolheu instalador único e KDE agora, Windows futuro.
- Decisão: preservar núcleo Python e UI QML/D-Bus. Distribuir instalador `.pyz`
  contendo fontes/widget; criar runtime próprio no usuário e ativação D-Bus ligada
  a unidade systemd de sessão, com reinício limitado. Nenhuma porta HTTP no modo local.
- Configuração: interface D-Bus Configuration1 assíncrona, PAT transitório até cofre,
  nunca em KConfig/JSON/logs. Seleção segura automática de Secret Service/KWallet;
  sem fallback em arquivo. Falhas de desbloqueio são exibidas pela interface.
- Seleção: ID persistente; índice antigo migra após descoberta válida. Um único AC
  é selecionado automaticamente; vários exigem escolha. Controle continua opt-in,
  agora disponível pela interface, com estado confirmado e domínio derivado do perfil.
- Compatibilidade: API HTTP/Docker preservados como alternativa avançada. Endpoint
  existente exige conversão explícita para local. Contrato AirConditioner1 permanece.
  Processos/arquivos antigos desconhecidos não são substituídos silenciosamente.
- Distribuição: sem dependência do checkout após instalação; Python/DBus/GLib/Plasma
  de sistema são pré-requisitos, detectados sem instalação global. Dependências
  Python são baixadas para venv próprio. Licença de redistribuição segue pendente.
- Windows: reutilizar núcleo de comunicação/regras; UI, transporte e cofre Windows
  precisam de implementação futura. Não se impõe homelab como pré-requisito.
- Limites: cofre real, novo login, atualização em plasmashell e controle físico
  dependem de aceitação manual. Não se declara Go com testes sintéticos.
