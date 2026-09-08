FROM node:24.20.0-slim@sha256:ba849c60be29959425b8734d57b8b4b7d56f98edd9504c9af091d5281095a71e AS dependencies

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

FROM node:24.20.0-slim@sha256:ba849c60be29959425b8734d57b8b4b7d56f98edd9504c9af091d5281095a71e AS runner

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
