# Testes e diagnóstico de desenvolvimento

## Preparar o ambiente

Use Python 3.11+ com dbus-python e PyGObject/GLib compatíveis instalados pela
distribuição. Instale os extras de desenvolvimento em um ambiente local:

```sh
python3 -m venv --system-site-packages .venv-runtime
.venv-runtime/bin/python -m pip install -e '.[dev,thinq,server,remote]'
```

Esses comandos exigem rede para instalar dependências; a CI não as instala.
São necessários bash, dbus-run-session, kpackagetool6, systemd-analyze, OpenSSL,
Qt 6 QtTest/qmllint, módulos QML do Plasma e gettext (xgettext/msgmerge/msgfmt).
Veja [dependências](DEPENDENCIES.md) e [compatibilidade](COMPATIBILITY.md).

## Integração contínua

Na raiz do checkout:

```sh
.venv-runtime/bin/python scripts/check_ci.py
```

A entrada executa Ruff, unidade, contratos, CLI simulada, QtTest, qmllint,
links/âncoras e sintaxe dos blocos shell, versões, ativação D-Bus sintética,
i18n e builds com validação dos ZIPs. Exemplos de instalação/nuvem nos documentos
são somente analisados, nunca executados. Confira contagens e skips no resultado
de cada execução; nenhum número histórico é requisito fixo.

Usa XDG/TMPDIR temporários e barramento privado sem catálogo de serviços do host.
Não reponta HOME, lê PAT ou acessa LG. Há HTTP em loopback, OpenSSL local, cofre fake
e ciclo real KPackage em packageroot temporária. Pip/venv e systemd do instalador
são simulados nos unitários; isso não comprova instalação real de dependências.
A integração usa processos sintéticos próprios para crash/reativação.

O runner é resolvido por `scripts/qt_tools.py`: `qmltestrunner6` no PATH, depois
`/usr/lib/qt6/bin/qmltestrunner`, ou caminho explícito em `LGTHINQ_QMLTESTRUNNER`.
O nome genérico no PATH pode ser Qt 5 e não é selecionado automaticamente.
Override inválido falha sem fallback; o caminho absoluto é transmitido aos filhos.

## Regressões específicas

```sh
PYTHONPATH=src .venv-runtime/bin/python -m unittest discover -s tests/unit -p test_c1_regressions.py -v
PYTHONPATH=src .venv-runtime/bin/python -m unittest discover -s tests/unit -p test_local.py -v
.venv-runtime/bin/python scripts/check_i18n.py
```

As regressões usam cópias temporárias com `.env`, `.env.local`, chaves e credenciais
sintéticas, arquivos desconhecidos, symlinks internos/externos e ZIPs adulterados.
Exigem inventário exato e falha ao faltar arquivo obrigatório, duplicar membro,
incluir symlink/tipo especial ou quebrar documentação/âncora do pacote.
Extraem pacotes com a fonte indisponível. Gettext exercita extração, merge,
compilação e lookup com contexto/singular/plural e sete casos de placeholder inválido.
A descoberta do runner cobre PATH alternativo, default, ausência e executáveis inválidos.

Testes do backend cobrem autenticação simulada, timeouts, cancelamento, reconexão,
comandos fora do domínio do perfil e preservação do último estado confirmado.
A falha de descoberta com engine existente deve aparecer no snapshot e permitir
recuperação. Fixtures nunca controlam hardware.

## Viewer e cenários adicionais

```sh
.venv-runtime/bin/python scripts/validate_phase0.py --production --check-config
.venv-runtime/bin/python scripts/validate_phase0.py --production --remote
.venv-runtime/bin/python scripts/validate_phase0.py --production --panel --temperature-edit --evidence-dir dist/visual-validation
```

O harness usa backend sintético e pode gravar logs/capturas no destino escolhido.
Escolha diretório novo para preservar resultados anteriores. Verifica handlers QML,
prévia/confirmação de temperatura e perda/retorno do serviço. Capturas de Item QML
não comprovam contornos compostos pelo desktop; foco/fechamento do viewer pode
interferir em cenários temporizados. A PoC tem [instruções próprias](../poc/phase-0-dbus/README.md).

Continuam ambientais: cofre real, login posterior, hardware, nuvem, temas,
compositor e demais versões Plasma/Qt. Não confundir simulação com essas validações.
Não executar `container_smoke.py` fora do contexto TLS sintético que ele exige.

## Regressões da revisão e pacotes Python internos

`tests/unit/test_review_regressions.py` cobre negação de controle efetiva em
serve-local, rejeição de overrides incompatíveis, defaults, seleção UI/CLI e
Refresh remoto pelo adaptador real com bus/engine fake. Nenhuma credencial real
ou endpoint LG é usado. Execute as validações em cópia isolada do checkout.

A CI também executa `scripts/check_python_packages.py`: wheel/sdist, wheel
reconstruído do sdist, inventários exatos, seleção dos dois catálogos Python e exclusão de recursos sentinela
e smoke instalado sem dependências. Requer setuptools>=68, wheel e pip existentes.
Se o Python da CI não os tiver, aponte `LGTHINQ_BUILD_PYTHON` para um venv de build
já preparado; não há instalação automática nem acesso ao índice. Por exemplo, na
cópia de teste, com a variável apontada ao ambiente existente:

```sh
.venv-runtime/bin/python scripts/check_python_packages.py --output dist/python-review
```

Escolha output novo: o checker recusa sobrescrever evidências. O subprocesso de
build usa esse Python separado; smoke usa o Python da CI em destino isolado. Build
técnico aprovado não autoriza distribuição independente ou conclui avisos/licenças.

## Candidata V1

Execute os comandos acima em cópia externa, com fontes selecionadas por manifesto,
sem os internos locais, e HOME/XDG/TMPDIR de teste. Não rode o instalador real nem
Docker para validar a candidata. Após as correções finais, uma rodada completa da
CI e os dois viewers (normal e `--compact-layout`) encerram a validação aplicável.
`test_i18n_runtime.py` carrega MO sintético pelo Ki18n real e pelo helper Python/zipapp;
os quatro catálogos do produto continuam sem traduções. Resultados simulados e
aceitação ambiental são registrados separadamente em [V1_READINESS](V1_READINESS.md).
