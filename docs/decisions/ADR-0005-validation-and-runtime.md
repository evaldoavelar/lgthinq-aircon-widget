# ADR-0005 — Runtime local e critérios de evidência

- Estado: implementado, transporte pendente de validação no desktop (2026-10-22).
- Contexto: PySide6 não está instalado; PyPI não resolve neste sandbox. dbus-python e PyGObject estão disponíveis no Python do sistema. O sandbox bloqueia sockets UNIX, inclusive o Session Bus e um barramento privado.
- Decisão: serviço D-Bus com dbus-python/GLib; backend assíncrono em thread dedicada. QML usa o módulo nativo instalado, sem C++, QProcess ou rede na UI. Python mínimo 3.11 pela semântica de timeout adotada. PySide6 deixou de ser necessário.
- Contrato: produção usa interface versionada AirConditioner1 e snapshots JSON (`s`) para capacidades variáveis e valores ausentes. A interface anterior fica exclusiva da PoC. Enfileirar um comando não significa sucesso do aparelho.
- Controle: simulação permite escrita; cliente real e capacidades publicadas permanecem somente leitura até teste especificamente autorizado. Não há chave CLI que habilite controle real acidentalmente.
- Credencial: Secret Service/KWallet explicitamente selecionado, sem fallback. HTTP session nasce e encerra no loop do backend. Polling conservador com backoff; MQTT não é necessário para a prova inicial.
- Consequências: dependências D-Bus/GLib precisam estar acessíveis ao Python escolhido; venv deve usar `--system-site-packages` no host. Não há portabilidade demonstrada em outro Linux. SDK e cofre reais ainda não foram exercitados.
- Evidência: qmllint e testes locais validam código/contrato, mas não substituem transporte e execução dentro do Plasma. A implementação das fases posteriores foi preparada como trabalho independente autorizado, sem aprovar o gate da Fase 0.

Atualização: transporte e dependências foram validados após liberação do ambiente.
Veja o [ADR-0006](ADR-0006-runtime-validation.md) para a decisão posterior e
[TESTING](../TESTING.md) para repetir a validação sintética. As limitações iniciais
acima são históricas; cofre real, LG e aceitação humana continuam gates separados.
