FROM python:3.13.7-slim@sha256:5f55cdf0c5d9dc1a415637a5ccc4a9e18663ad203673173b8cda8f8dcacef689 AS dependencies

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    UV_LINK_MODE=copy

WORKDIR /workspace
RUN python -m pip install --no-cache-dir uv==0.12.9
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --group dev --no-install-project

FROM python:3.13.7-slim@sha256:5f55cdf0c5d9dc1a415637a5ccc4a9e18663ad203673173b8cda8f8dcacef689 AS runner

ENV PATH="/workspace/.venv/bin:${PATH}" \
    PYTHONPATH="/workspace/apps/api" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN groupadd --system --gid 10001 savepoint \
    && useradd --system --uid 10001 --gid savepoint --create-home savepoint
WORKDIR /workspace
COPY --from=dependencies --chown=savepoint:savepoint /workspace/.venv /workspace/.venv
COPY --chown=savepoint:savepoint apps/api ./apps/api
# The deployment pre-release import is intentionally offline. Compose mounts
# these directories read-only in development; the immutable production image
# must carry the same frozen inputs because no host bind mount exists on a
# PaaS. docs/ is required too: import_catalogue's fail-closed freeze check
# reads docs/verification/catalogue-freeze.md, which previously only existed
# via the local-only Compose bind mount and was missing from the image,
# breaking every deploy at the first startup command.
COPY --chown=savepoint:savepoint data ./data
COPY --chown=savepoint:savepoint docs ./docs
RUN ln -s /workspace/apps/api/manage.py /workspace/manage.py
USER 10001:10001
CMD ["pytest", "apps/api/tests", "-q"]
