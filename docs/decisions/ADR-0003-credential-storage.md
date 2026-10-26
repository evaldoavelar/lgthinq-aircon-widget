# ADR-0003 — Armazenamento seguro do PAT

- **Estado:** princípio aceito; implementação pendente.
- **Contexto:** PAT é segredo bearer; exposição permite uso até revogação/expiração.
- **Decisão:** nunca armazenar senha LG. Preferir KWallet/Secret Service via backend suportado por `keyring`; tratar cofre indisponível como erro explícito.
- **Alternativas:** PAT em arquivo protegido; PAT em variável de ambiente; inserir o token no prompt/código.
- **Consequências:** menor persistência acidental; primeiro uso depende do backend de segredo estar disponível. Fallback em arquivo não é automático e requer autorização e revisão.
- **Segurança:** tokens nunca entram no Git, logs, fixtures ou relatórios.
