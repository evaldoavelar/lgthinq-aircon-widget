# Contribuir durante a preparação para publicação

Código próprio é GPL-3.0-or-later; prosa própria é CC BY 4.0.
Leia [LICENSING](docs/LICENSING.md) e [TESTING](docs/TESTING.md).

Antes de enviar uma contribuição, identifique autoria, origem e eventuais trechos
adaptados; mantenha avisos de terceiros. Não inclua recursos visuais de origem
incerta, APKs, dumps de dispositivo ou segredos. Envie contribuições próprias
sob a licença aplicável ao arquivo; não se presume cessão de direitos.

Preserve capacidades dinâmicas, operações de rede fora da renderização e confirmação
de estado após comando. Use dados sintéticos e nunca acione equipamento na automação.
Registre comandos, resultados e skips. Uma mudança de UI deve passar por qmllint e
QtTest; mudanças no backend exigem os testes pertinentes de unidade/contrato.

Para revisão local, use a entrada [de CI independente de hospedagem](docs/TESTING.md#integração-contínua).
Separe alteração funcional de tradução e de licenciamento. O plano de inglês/pt_BR
está em [I18N](docs/I18N.md). Não traduza identificadores D-Bus ou nomes da API LG.

Use issues e pull requests deste repositório. Relatos devem incluir versões, reprodução sintética e erros
sanitizados. Para segurança, combine um canal privado antes de transmitir detalhes;
nunca publique PAT, cabeçalhos, IDs privados ou respostas brutas.
