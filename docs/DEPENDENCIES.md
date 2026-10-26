# Dependências e evidências de licença

Snapshot local de 2026-10-23, Python 3.14/Linux. Não é lockfile nem certificação dos binários.
O projeto não declara dependências básicas; extras em pyproject.toml e runtime do sistema
fornecem os componentes. Versões abaixo foram lidas dos metadados instalados, não resolvidas
novamente. Não inclui todos os pacotes do host, apenas os usados pelo projeto e suas transitivas.
As licenças e nomes de autores são declarações upstream; não substituem direitos próprios.

| Componente | Versão observada | Autor declarado / origem | Licença declarada | Evidência instalada |
|---|---|---|---|---|
| `thinqconnect` | 1.0.14 | ThinQConnect; [origem](https://github.com/thinq-connect/pythinqconnect) | Apache-2.0 (classifier + LICENSE) | `thinqconnect-1.0.14.dist-info/licenses/LICENSE` |
| `keyring` | 25.7.0 | Kang Zhang <jobo.zh@gmail.com>; [origem](https://github.com/jaraco/keyring) | MIT | `keyring-25.7.0.dist-info/licenses/LICENSE` |
| `aiohttp` | 3.14.5 | Colaboradores upstream; campo Author ausente; [origem](https://github.com/aio-libs/aiohttp) | Apache-2.0 AND MIT | `aiohttp-3.14.5.dist-info/licenses/LICENSE.txt`, `aiohttp-3.14.5.dist-info/licenses/vendor/llhttp/LICENSE` |
| `awsiotsdk` | 1.31.0 | AWS SDK Common Runtime Team; [origem](https://github.com/aws/aws-iot-device-sdk-python-v2) | License :: OSI Approved :: Apache Software License | Metadados; pacote do sistema ou texto upstream a complementar |
| `awscrt` | 0.36.1 | "Amazon Web Services, Inc" <aws-sdk-common-runtime@amazon.com>; [origem](https://github.com/awslabs/aws-crt-python) | Apache-2.0 | `awscrt-0.36.1.dist-info/licenses/LICENSE`, `awscrt-0.36.1.dist-info/licenses/NOTICE` |
| `cryptography` | 50.0.2 | The Python Cryptographic Authority and individual contributors <cryptography-dev@python.org>; [origem](https://github.com/pyca/cryptography) | Apache-2.0 OR BSD-3-Clause | `cryptography-50.0.2.dist-info/licenses/LICENSE`, `cryptography-50.0.2.dist-info/licenses/LICENSE.APACHE`, `cryptography-50.0.2.dist-info/licenses/LICENSE.BSD` |
| `cffi` | 2.1.1 | Armin Rigo, Maciej Fijalkowski; [origem](https://github.com/python-cffi/cffi) | MIT-0 | `cffi-2.1.1.dist-info/licenses/LICENSE` |
| `pycparser` | 3.12 | Eli Bendersky <eliben@gmail.com>; [origem](https://github.com/eliben/pycparser) | BSD-3-Clause | `pycparser-3.12.dist-info/licenses/LICENSE` |
| `aiohappyeyeballs` | 2.7.1 | J. Nick Koston; [origem](https://github.com/aio-libs/aiohappyeyeballs) | PSF-2.0 | `aiohappyeyeballs-2.7.1.dist-info/licenses/LICENSE` |
| `aiosignal` | 1.4.0 | Colaboradores upstream; campo Author ausente; [origem](https://github.com/aio-libs/aiosignal) | Apache 2.0 | `aiosignal-1.4.0.dist-info/licenses/LICENSE` |
| `frozenlist` | 1.8.0 | Colaboradores upstream; campo Author ausente; [origem](https://github.com/aio-libs/frozenlist) | Apache-2.0 | `frozenlist-1.8.0.dist-info/licenses/LICENSE` |
| `multidict` | 7.1.0 | Andrew Svetlov <andrew.svetlov@gmail.com>; [origem](https://github.com/aio-libs/multidict) | Apache-2.0 | `multidict-7.1.0.dist-info/licenses/LICENSE` |
| `yarl` | 1.25.1 | Andrew Svetlov; [origem](https://github.com/aio-libs/yarl) | Apache-2.0 | `yarl-1.25.1.dist-info/licenses/LICENSE`, `yarl-1.25.1.dist-info/licenses/NOTICE` |
| `propcache` | 0.5.4 | Andrew Svetlov; [origem](https://github.com/aio-libs/propcache) | Apache-2.0 | `propcache-0.5.4.dist-info/licenses/LICENSE`, `propcache-0.5.4.dist-info/licenses/NOTICE` |
| `attrs` | 26.1.0 | Hynek Schlawack <hs@ox.cx>; [origem](https://pypi.org/project/attrs/26.1.0/) | MIT | `attrs-26.1.0.dist-info/licenses/LICENSE` |
| `idna` | 3.20 | Kim Davies <kim+pypi@gumleaf.org>; [origem](https://github.com/kjd/idna) | BSD-3-Clause | `idna-3.20.dist-info/licenses/LICENSE.md` |
| `SecretStorage` | 3.5.0 | Dmitry Shachnev <mitya57@gmail.com>; [origem](https://github.com/mitya57/secretstorage) | BSD-3-Clause | `secretstorage-3.5.0.dist-info/licenses/LICENSE` |
| `jeepney` | 0.9.0 | Thomas Kluyver <thomas@kluyver.me.uk>; [origem](https://gitlab.com/takluyver/jeepney) | MIT | `jeepney-0.9.0.dist-info/licenses/LICENSE` |
| `jaraco.classes` | 3.4.0 | Jason R. Coombs; [origem](https://github.com/jaraco/jaraco.classes) | MIT (classifier + LICENSE) | `jaraco.classes-3.4.0.dist-info/LICENSE` |
| `jaraco.context` | 6.1.2 | "Jason R. Coombs" <jaraco@jaraco.com>; [origem](https://github.com/jaraco/jaraco.context) | MIT | `jaraco_context-6.1.2.dist-info/licenses/LICENSE` |
| `jaraco.functools` | 4.6.0 | "Jason R. Coombs" <jaraco@jaraco.com>; [origem](https://github.com/jaraco/jaraco.functools) | MIT | `jaraco_functools-4.6.0.dist-info/licenses/LICENSE` |
| `more-itertools` | 11.2.1 | Erik Rose <erikrose@grinchcentral.com>; [origem](https://github.com/more-itertools/more-itertools) | MIT | `more_itertools-11.2.1.dist-info/licenses/LICENSE` |
| `dbus-python` | 1.5.0 | Colaboradores upstream; campo Author ausente; [origem](http://www.freedesktop.org/wiki/Software/DBusBindings/#python) | MIT AND (GPL-2.0-or-later OR AFL-2.1) | Metadados; pacote do sistema ou texto upstream a complementar |
| `PyGObject` | 3.58.1 | James Henstridge <james@daa.com.au>; [origem](https://pygobject.gnome.org) | LGPL-2.1-or-later | Metadados; pacote do sistema ou texto upstream a complementar |
| `pytest` | 9.1.1 | Brianna Laugher, Bruno Oliveira, Floris Bruynooghe, Freya Bruhin, Holger Krekel, Others (See AUTHORS), Ronny Pfannschmidt; [origem](https://docs.pytest.org/en/latest/) | MIT | `pytest-9.1.1.dist-info/licenses/LICENSE` |
| `ruff` | 0.17.2 | "Astral Software Inc." <hey@astral.sh>; [origem](https://docs.astral.sh/ruff) | MIT | `ruff-0.17.2.dist-info/licenses/LICENSE` |
| `pip` | 26.2.1 | The pip developers <distutils-sig@python.org>; [origem](https://pip.pypa.io/) | MIT | `pip-26.2.1.dist-info/licenses/AUTHORS.txt`, `pip-26.2.1.dist-info/licenses/LICENSE.txt`, `pip-26.2.1.dist-info/licenses/src/pip/_vendor/cachecontrol/LICENSE.txt`, `pip-26.2.1.dist-info/licenses/src/pip/_vendor/certifi/LICENSE`, `pip-26.2.1.dist-info/licenses/src/pip/_vendor/distlib/LICENSE.txt`, `pip-26.2.1.dist-info/licenses/src/pip/_vendor/distro/LICENSE`, `pip-26.2.1.dist-info/licenses/src/pip/_vendor/idna/LICENSE.md`, `pip-26.2.1.dist-info/licenses/src/pip/_vendor/msgpack/COPYING`, `pip-26.2.1.dist-info/licenses/src/pip/_vendor/packaging/LICENSE`, `pip-26.2.1.dist-info/licenses/src/pip/_vendor/packaging/LICENSE.APACHE`, `pip-26.2.1.dist-info/licenses/src/pip/_vendor/packaging/LICENSE.BSD`, `pip-26.2.1.dist-info/licenses/src/pip/_vendor/pkg_resources/LICENSE`, `pip-26.2.1.dist-info/licenses/src/pip/_vendor/platformdirs/LICENSE`, `pip-26.2.1.dist-info/licenses/src/pip/_vendor/pygments/LICENSE`, `pip-26.2.1.dist-info/licenses/src/pip/_vendor/pyproject_hooks/LICENSE`, `pip-26.2.1.dist-info/licenses/src/pip/_vendor/requests/LICENSE`, `pip-26.2.1.dist-info/licenses/src/pip/_vendor/resolvelib/LICENSE`, `pip-26.2.1.dist-info/licenses/src/pip/_vendor/rich/LICENSE`, `pip-26.2.1.dist-info/licenses/src/pip/_vendor/tomli/LICENSE`, `pip-26.2.1.dist-info/licenses/src/pip/_vendor/tomli_w/LICENSE`, `pip-26.2.1.dist-info/licenses/src/pip/_vendor/truststore/LICENSE`, `pip-26.2.1.dist-info/licenses/src/pip/_vendor/urllib3/LICENSE.txt` |

## Dependências de build e condicionais

- setuptools>=68 e wheel: requisitos de build; versões efetivas reobservadas no ambiente externo: setuptools 84.2.1 e wheel 0.48.0.
  [Setuptools](https://github.com/pypa/setuptools/blob/main/LICENSE),
  [wheel](https://github.com/pypa/wheel/blob/main/LICENSE.txt). Não instalados neste venv.
  A revisão independente posterior criou uma venv externa exclusiva com build,
  setuptools e wheel e registrou suas versões nos artefatos de auditoria. O build
  wheel/sdist e smoke sintético do wheel passaram ali; esta venv original foi preservada.
- pytest/Ruff são ferramentas de desenvolvimento; seus próprios auxiliares não são payload
  do produto. Se um ambiente de desenvolvimento for redistribuído, inventariá-lo separadamente.
- Python anterior a 3.13/3.12 pode resolver typing_extensions, importlib_metadata,
  backports.tarfile e transitivas; Windows adiciona componentes de cofre próprios.
  Versões/licenças dessas resoluções continuam pendentes antes de declarar suporte/distribuí-las.

## Obrigações e pendências por família

| Família / componente | Obrigações / situação |
|---|---|
| Apache-2.0 | Preservar licença, atribuições e NOTICE pertinente; identificar modificações. Compatível com GPLv3, não com GPLv2 isoladamente |
| MIT / BSD / PSF | Preservar avisos, condições e disclaimers aplicáveis; observar a condição de não endosso BSD |
| aiohttp | Apache-2.0 AND MIT: llhttp tem copyright Fedor Indutny e licença própria |
| awsiotsdk | LICENSE/NOTICE não constam do wheel; licença Apache comprovada nos documentos da tag v1.31.0, que precisam acompanhar a redistribuição pertinente |
| awscrt | NOTICE incorpora xxHash BSD-2-Clause, copyright Yann Collet; inventário dos nativos pendente |
| cryptography | Apache-2.0 OR BSD-3-Clause para o componente principal; OpenSSL/nativos/Rust separados, revisão pendente |
| cffi | MIT-0 principal; conferir bibliotecas e exceções do binário, sem presumir que todas sejam MIT-0 |
| dbus-python | Metadata composta MIT AND (GPL-2.0-or-later OR AFL-2.1); COPYING do sistema distingue dbus-gmain |
| PyGObject/GLib e KDE/Qt | Requisitos do sistema; preservar LGPL/GPL/alternativas por arquivo se forem redistribuídos; não embutidos nos ZIPs atuais |
| pip | MIT no principal; bibliotecas vendorizadas têm termos próprios, incluindo certifi/MPL-2.0. Não extrapolar MIT para todo o pacote |

Fontes AWS fixadas: [SDK LICENSE](https://github.com/aws/aws-iot-device-sdk-python-v2/blob/v1.31.0/documents/LICENSE),
[SDK NOTICE](https://github.com/aws/aws-iot-device-sdk-python-v2/blob/v1.31.0/documents/NOTICE),
[CRT NOTICE](https://github.com/awslabs/aws-crt-python/blob/v0.36.1/NOTICE).

A base Docker tem inventário separado e ainda não encerrado em
[DOCKER_COMPLIANCE](DOCKER_COMPLIANCE.md). Não há conclusão de conformidade integral.
Para o mapa de avisos por artefato, consulte [DISTRIBUTION](DISTRIBUTION.md).

## Limites do inventário

A tabela descreve a resolução observada em Python 3.14.8, não um lock para todas
as plataformas. Metadados e presença de arquivos de licença podem ser inspecionados
sem importar SDKs ou acessar a nuvem. Um nome de licença no metadata não demonstra
conformidade do binário completo; awscrt, cryptography/OpenSSL e outros nativos
exigem mapa de componentes/fontes próprio. Os ZIPs do projeto não embutem esses
wheels: o instalador resolve dependências via pip. Redistribuir um ambiente ou
imagem contendo essas dependências exige examinar os termos desse novo payload.

## Revalidação após a consolidação

Metadados e LICENSE/NOTICE do ambiente runtime foram relidos, sem importar SDK,
resolver/instalar pacotes nem acessar LG. As versões da tabela foram reconfirmadas;
iniconfig 2.3.1, pluggy 1.7.0, packaging 26.3 e Pygments 2.21.0 foram identificados
como auxiliares instalados de desenvolvimento. O ambiente externo de build contém
build 1.6.1, pyproject-hooks 1.3.3, setuptools 84.2.1, wheel 0.48.0, packaging 26.3 e
pip 26.2.1. Seus textos legais e declarações estão inventariados externamente;
setuptools também contém avisos de terceiros, não só seu LICENSE principal.

O script de inspeção `scripts/audit_distribution.py dependencies --output CAMINHO_NOVO`
gera versões, declarações diretas/extras, Requires-Dist brutos, URLs declaradas,
hashes dos textos legais e extensões nativas. Não importa bibliotecas ou consulta
o índice. Mantém candidatos condicionais/extra sem avaliar markers: pacote ausente
nessa lista não é automaticamente dependência faltante do produto. Não é lock,
SBOM binária completa nem inventário integral do host. Executar separadamente com
o interpretador de runtime e de build; bindings do sistema podem não listar
arquivos em RECORD e exigir inventário do gerenciador de pacotes.

thinqconnect usa a tag **1.0.14**, sem prefixo v:
[LICENSE primário](https://github.com/thinq-connect/pythinqconnect/blob/1.0.14/LICENSE).
O texto adquirido corresponde ao LICENSE instalado; a tentativa de tag v1.0.14
retornou 404 e foi registrada, sem inferir ausência de licença. AWS LICENSE e NOTICE
v1.31.0 foram adquiridos novamente e coincidem com a preservação anterior;
o wheel instalado continua sem esses dois textos. Não se alterou o ambiente para
aparentar conformidade. As 13 revisões nativas de awscrt e os 40 registros Cargo
candidatos de cryptography estão delimitados em [NATIVE_COMPONENTS](NATIVE_COMPONENTS.md).

Formatos sem bundle não incorporam essas bibliotecas. Docker e eventual runtime
redistribuído exigem análise dos próprios bytes conforme [ARTIFACT_NOTICES](ARTIFACT_NOTICES.md).
Não foram criados locks/digests fictícios: a resolução histórica não certifica
compatibilidade de uma nova resolução ou de Python 3.11–3.13.
