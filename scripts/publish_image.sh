#!/usr/bin/env bash
# Local build/smoke only while distribution rights and compliance remain unresolved.
set -euo pipefail
if [[ ${1:-} == --help ]]; then
    echo 'Usage: scripts/publish_image.sh --build-only'
    echo 'Publication suspended: see docs/DOCKER_COMPLIANCE.md and docs/LICENSING.md.'
    exit 0
fi
if [[ $# -ne 1 || $1 != --build-only ]]; then
    echo 'Publication suspended: rights and Docker compliance require human resolution.' >&2
    exit 2
fi
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$root"
command -v docker >/dev/null
command -v openssl >/dev/null
docker info >/dev/null
tag="homelab-$(date -u +%Y%m%d-%H%M%S)"
image="localhost/lgthinq:$tag"
mkdir -p dist
docker build --platform linux/amd64 -f packaging/docker/Dockerfile -t "$image" .
tls=$(mktemp -d "$root/dist/smoke-tls.XXXXXXXX")
trap 'rm -rf -- "$tls"' EXIT
# Synthetic test key, never a deployment key. Readable by the unprivileged test container.
openssl req -x509 -newkey rsa:2048 -nodes -days 1 -subj /CN=localhost \
    -addext 'subjectAltName=DNS:localhost,IP:127.0.0.1' \
    -keyout "$tls/server.key" -out "$tls/server.crt" >/dev/null 2>&1
chmod 755 "$tls"
chmod 444 "$tls/server.key" "$tls/server.crt"
docker run --rm -i --network none --read-only --cap-drop ALL \
    --security-opt no-new-privileges --tmpfs /tmp:rw,noexec,nosuid,size=16m \
    --mount "type=bind,source=$tls,target=/smoke-tls,readonly" \
    --entrypoint python "$image" - < tests/integration/container_smoke.py
echo "Validated locally: $image (publication remains suspended)"
