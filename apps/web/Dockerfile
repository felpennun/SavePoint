FROM node:26.8.2-slim@sha256:f7bb8247fdb16250dbec7fd0e24f091c6f5f0a29d256f3aef5816a7a369166b2 AS dependencies

ENV COREPACK_HOME=/opt/corepack
WORKDIR /workspace
RUN corepack enable \
    && corepack prepare pnpm@11.26.0 --activate \
    && chmod 0755 /opt/corepack/v1/pnpm/11.26.0/bin/pnpm.cjs \
    && rm -rf /usr/local/lib/node_modules/npm /usr/local/lib/node_modules/corepack \
    && rm -f /usr/local/bin/npm /usr/local/bin/npx /usr/local/bin/corepack \
        /usr/local/bin/yarn /usr/local/bin/yarnpkg /usr/local/bin/pnpm /usr/local/bin/pnpx \
    && ln -s /opt/corepack/v1/pnpm/11.26.0/bin/pnpm.cjs /usr/local/bin/pnpm
COPY --chown=node:node package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY --chown=node:node apps/web/package.json ./apps/web/package.json
RUN pnpm install --frozen-lockfile --ignore-scripts

FROM node:26.8.2-slim@sha256:f7bb8247fdb16250dbec7fd0e24f091c6f5f0a29d256f3aef5816a7a369166b2 AS runner

ENV COREPACK_HOME=/opt/corepack \
    NODE_ENV=test \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
WORKDIR /workspace
RUN corepack enable \
    && corepack prepare pnpm@11.26.0 --activate \
    && chmod 0755 /opt/corepack/v1/pnpm/11.26.0/bin/pnpm.cjs \
    && rm -rf /usr/local/lib/node_modules/npm /usr/local/lib/node_modules/corepack \
    && rm -f /usr/local/bin/npm /usr/local/bin/npx /usr/local/bin/corepack \
        /usr/local/bin/yarn /usr/local/bin/yarnpkg /usr/local/bin/pnpm /usr/local/bin/pnpx \
    && ln -s /opt/corepack/v1/pnpm/11.26.0/bin/pnpm.cjs /usr/local/bin/pnpm
COPY --from=dependencies --chown=node:node /workspace/node_modules ./node_modules
COPY --chown=node:node package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY --chown=node:node apps/web ./apps/web

# Keep the test/runtime image able to launch the pinned Playwright Chromium.
# These are Debian bookworm runtime libraries; the browser itself remains
# supplied by the repository's Playwright bootstrap rather than a global install.
USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        fonts-liberation \
        libasound2 \
        libatk-bridge2.0-0 \
        libatk1.0-0 \
        libatspi2.0-0 \
        libc6 \
        libcairo2 \
        libcups2 \
        libdbus-1-3 \
        libdrm2 \
        libgbm1 \
        libglib2.0-0 \
        libgtk-3-0 \
        libnspr4 \
        libnss3 \
        libpango-1.0-0 \
        libx11-6 \
        libx11-xcb1 \
        libxcb1 \
        libxcomposite1 \
        libxdamage1 \
        libxext6 \
        libxfixes3 \
        libxkbcommon0 \
        libxrandr2 \
        libxshmfence1 \
        xdg-utils \
    && rm -rf /var/lib/apt/lists/*
RUN mkdir -p /ms-playwright \
    && pnpm --dir apps/web exec playwright install chromium \
    && chmod -R a+rX /ms-playwright
USER node
CMD ["pnpm", "--dir", "apps/web", "test", "--run"]
