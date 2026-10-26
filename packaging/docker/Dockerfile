FROM python:3.14-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY pyproject.toml BACKEND.md MANIFEST.in LICENSE LICENSE-DOCS NOTICE ./
COPY src ./src
# Container has no D-Bus or keyring dependency. SDK currently brings AWS libraries.
RUN python -m pip install '.[server]' 'thinqconnect==1.0.14' \
    && groupadd --gid 10001 lgthinq \
    && useradd --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin lgthinq
USER 10001:10001
EXPOSE 8765
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8765/healthz', timeout=3).read()" || exit 1
ENTRYPOINT ["python", "-m", "lgthinq_daemon.container_server"]
