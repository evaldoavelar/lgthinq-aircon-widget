# ThinQ Connect — implementação e limites

Verificação das fontes upstream em 2026-10-22: o repositório chama-se
`pythinqconnect`, porém a distribuição/importação são **thinqconnect**. O extra
`thinq` fixa 1.0.14 conforme setup.py consultado. A instalação efetiva foi concluída em `.venv-runtime` após liberação do ambiente;
as assinaturas do pacote instalado foram conferidas por inspect.signature.

Fontes primárias consultadas:
- [SDK e inicialização](https://github.com/thinq-connect/pythinqconnect)
- [Transporte público](https://github.com/thinq-connect/pythinqconnect/blob/main/thinqconnect/thinq_api.py)
- [Perfil do AC](https://github.com/thinq-connect/pythinqconnect/blob/main/thinqconnect/devices/air_conditioner.py)
- [Parser de propriedades](https://github.com/thinq-connect/pythinqconnect/blob/main/thinqconnect/devices/connect_device.py)
- [Versão e dependências](https://github.com/thinq-connect/pythinqconnect/blob/main/setup.py)

A integração usa o cliente assíncrono público para descoberta, perfil, estado e
controle. A implementação tem testes sintéticos; isso não valida controle físico
nem compatibilidade com todos os modelos.
Não se infere incompatibilidade a partir de lista vazia. MQTT não foi integrado.

## Configuração segura

Instale localmente quando a rede estiver disponível:

```sh
.venv/bin/python -m pip install -e '.[thinq,dev]'
```

Configure explicitamente backend Secret Service ou KWallet suportado por keyring;
a implementação rejeita backend plaintext, fail e chainer. Sem cofre, retorna erro,
sem fallback em arquivo ou variável de ambiente. O comando abaixo solicita PAT
por entrada oculta em terminal privado, nunca argumento de linha de comando:

```sh
PYTHONPATH=src .venv/bin/python -m lgthinq_daemon credential-set
```

Obtenha PAT no [portal LG](https://connect-pat.lgthinq.com/) fora da conversa.
Gere um UUID uma única vez (`python3 -m uuid`) e reutilize como client ID;
use código do país da conta. O ID não é token, mas é específico da instalação.

```sh
PYTHONPATH=src .venv/bin/python -m lgthinq_daemon --client-id UUID --country BR discover
PYTHONPATH=src .venv/bin/python -m lgthinq_daemon --client-id UUID --country BR --device-index 0 status
```

Descoberta imprime contagem e tipos sanitizados, omitindo IDs/aliases. Use o índice retornado por `discover` para selecionar o aparelho em
`status`; listas podem mudar, portanto confira o tipo antes de selecionar. A CLI
não despeja resposta bruta. O comando status emite apenas estado/capacidades normalizados, sem
perfil completo, ID ou cabeçalhos. Não compartilhe saídas sem revisão de privacidade.
Modelo comercial específico não é preservado no snapshot; consulta bruta do perfil
existe no adaptador, mas sua normalização de metadados permanece pendente.

## Simulação reproduzível

```sh
PYTHONPATH=src python3 -m lgthinq_daemon --simulate status
PYTHONPATH=src python3 -m lgthinq_daemon --simulate command temperatureInUnits.targetTemperature.C 25
PYTHONPATH=src python3 -m lgthinq_daemon --simulate serve
PYTHONPATH=src python3 -m unittest discover -s tests/unit -v
```

`serve` depende de dbus-python/GLib e Session Bus. A leitura reportada pelo usuário
não comprova o ciclo completo do serviço na sessão real nem controle físico.
Encerre com Ctrl+C; não instala nem habilita serviço. Cada invocação da CLI simula
um aparelho novo. Fixtures são sintéticas no módulo client e não refletem o aparelho.

Capacidades provêm exclusivamente de `profile.property`, modos explícitos e domínio
de escrita. Temperaturas em unidades distintas têm chaves distintas. Domínios
incompletos permanecem sem controle; nenhuma faixa padrão é inventada. Recursos
não mapeáveis ficam ausentes. Estado só muda depois de consulta confirmatória.

O adaptador serializa chamadas, aplica timeout/cancelamento e intervalo mínimo
conservador de um segundo (não representa limite oficial LG). Monitoramento aplica
backoff até 15 minutos; autenticação exige intervenção e suspende retries.
Erros separam autenticação, região, ausência de aparelho, falta de suporte, limite
de chamadas, rede e operação. Exceções SDK com cabeçalhos privados não são expostas.
Controle real é recusado pela CLI e pelo adaptador por padrão; nenhum teste altera
hardware. Daemon com sessão aiohttp real foi implementado com criação/fechamento no loop do backend, mas permanece sem validação de integração. Comandos reais ficam bloqueados por padrão e são liberados pelo operador com
`--allow-control` ou `"allow_control": true` no servidor Docker. SDK opcional também traz dependências AWS/MQTT,
embora este projeto não ative eventos nem registre clientes na nuvem.

## Licenciamento e proveniência

thinqconnect 1.0.14 declara Apache-2.0 no LICENSE distribuído e nos cabeçalhos LG
Electronics. O campo simples License vazio não equivale a ausência de licença.
O extra também resolve aiohttp, awsiotsdk e cryptography: preservar suas condições
próprias. A auditoria confirmou correspondência dos 47 fontes Python instalados com
o wheel do PyPI, sem atestação de proveniência comprovada. Veja
[LICENSING](LICENSING.md) e o [inventário](DEPENDENCIES.md). Licença do SDK não
concede automaticamente direitos sobre marcas LG ou uso da API fora de seus termos.
