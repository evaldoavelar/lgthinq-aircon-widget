# Evolução do LG ThinQ AirCon Widget

A candidata V1 se limita a ar-condicionado LG ThinQ em KDE Plasma 6. A preparação
técnica e os gates externos estão separados em [V1_READINESS](V1_READINESS.md).

| Categoria | Próxima ação mínima |
|---|---|
| Distribuição pública autorizada | Manter GPL-3.0-or-later/CC BY 4.0 e avisos nos pacotes; preservar direitos e atribuições de terceiros |
| Pendência jurídica de distribuição | Resolver separadamente fonte correspondente e tratamento da imagem Docker histórica; nenhuma publicação autorizada |
| Pendência de tradução | Revisar/redigir inglês e pt_BR nos POs preparados; fontes atuais mistas, sem traduções aprovadas |
| Pendência de validação ambiental | Cofre real com segredo sintético, novo login, versões/temas Plasma e aceitação manual LG sob autorização própria |
| Melhoria futura fora do escopo | Interface Windows com cofre e ciclo de processo próprios; interface GNOME e outros ambientes |
| Melhoria futura fora do escopo | Resoluções com hashes, base fixa, reprodução byte a byte e matriz ampliada de CI |

Novas plataformas reutilizam o núcleo descrito em [arquitetura](ARCHITECTURE.md).
Nenhuma delas é suporte funcional atual. MQTT e protocolos privados não são
pré-requisitos da integração oficial. Não há plano de expandir V1 a outras marcas
ou tipos de aparelhos.
