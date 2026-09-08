FROM node:26.8.1-slim@sha256:c0753125a3789977aefe869cbebccf70e3cfd7ea84ca48547458f02e4f1d7146 AS dependencies

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

FROM node:26.8.1-slim@sha256:c0753125a3789977aefe869cbebccf70e3cfd7ea84ca48547458f02e4f1d7146 AS runner

ENV COREPACK_HOME=/opt/corepack \
    NODE_ENV=test
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
USER node
CMD ["pnpm", "--dir", "apps/web", "test", "--run"]
