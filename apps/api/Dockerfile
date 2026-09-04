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
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN groupadd --system --gid 10001 savepoint \
    && useradd --system --uid 10001 --gid savepoint --create-home savepoint
WORKDIR /workspace
COPY --from=dependencies --chown=savepoint:savepoint /workspace/.venv /workspace/.venv
COPY --chown=savepoint:savepoint apps/api ./apps/api
USER 10001:10001
CMD ["pytest", "apps/api/tests", "-q"]

