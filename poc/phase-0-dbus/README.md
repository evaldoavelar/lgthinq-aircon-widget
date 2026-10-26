# Fase 0 — PoC local bidirecional

Implementação corrigida e **IPC aprovado por automação no plasmoidviewer/Wayland**.
Sem LG, PAT, rede ou controle real. Requer Python do sistema com dbus-python e
PyGObject, Plasma com módulo workspace.dbus e plasmoidviewer.

Execução manual na sessão KDE (dois terminais):

```sh
python3 poc/phase-0-dbus/service/poc_dbus_service.py --demo-tick
plasmoidviewer -a ./poc/phase-0-dbus/plasmoid
```

O tick alterna temperatura sintética entre 23 e 24 a cada cinco segundos. Observe
mudança no QML. Clique energia/temperatura, confira log Python e retorno na UI.
Pare servidor com Ctrl+C; confirme aviso e controles desabilitados. Reinicie e
confira recuperação. Feche viewer para encerrar. Nenhum serviço foi instalado.

Teste automatizado isolado:

```sh
python3 scripts/validate_phase0.py
# Complemento headless, sem substituir execução visual:
python3 scripts/validate_phase0.py --offscreen
```

O script cria cópia temporária do Plasmoid, injeta acionamento QML sintético após
7s, confirma sinal de tick independente, método QML→Python e sinal de retorno.
Verifica introspecção e sobrevivência do viewer após serviço parar. O acionamento
automático usa a mesma função do botão; clique humano ainda deve ser conferido.
Logs e processos ficam isolados e são limpos ao sair. Não altera o pacote original.

Contrato detalhado em `docs/DBUS_CONTRACT.md`. Só a PoC usa limite fictício 10–35.
Propriedades somente leitura em Get/GetAll; mudanças publicam StateChanged e
PropertiesChanged. QML usa SignalWatcher e chamadas assíncronas com assinatura `(d)`
ou `(b)`, com propriedades de representação no próprio PlasmoidItem.

Histórico da primeira tentativa: import do serviço OK; dois testes locais de objeto/
introspecção OK; qmllint sem avisos. Naquela tentativa o transporte não foi demonstrado: Session Bus recusou socket
com EPERM; dbus-run-session também não conseguiu criar socket privado; viewer
terminou com código 1. Aquela tentativa não satisfez o gate; a reexecução abaixo o demonstrou.

Atualização: após liberação, o harness passou tick independente, handler de botão,
retorno confirmado e reconexão. Use `--evidence-dir dist/phase0-validation` para salvar
logs. A automação aciona o sinal clicked do botão; avaliação humana do clique físico
e aparência continua complementar. Veja o guia `docs/TESTING.md`;
a descrição anterior do sandbox é histórica.
