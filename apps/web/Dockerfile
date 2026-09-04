FROM node:24.13.0-slim@sha256:4660b1ca8b28d6d1906fd644abe34b2ed81d15434d26d845ef0aced307cf4b6f AS dependencies

ENV COREPACK_HOME=/opt/corepack
WORKDIR /workspace
RUN corepack enable && corepack prepare pnpm@11.25.0 --activate
COPY --chown=node:node package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY --chown=node:node apps/web/package.json ./apps/web/package.json
RUN pnpm install --frozen-lockfile --ignore-scripts
COPY --chown=node:node types ./types
RUN mkdir -p node_modules/@types && cp -r types/shims/@types/* node_modules/@types/

FROM node:24.13.0-slim@sha256:4660b1ca8b28d6d1906fd644abe34b2ed81d15434d26d845ef0aced307cf4b6f AS runner

ENV COREPACK_HOME=/opt/corepack \
    NODE_ENV=test
WORKDIR /workspace
RUN corepack enable && corepack prepare pnpm@11.25.0 --activate
COPY --from=dependencies --chown=node:node /workspace/node_modules ./node_modules
COPY --chown=node:node package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY --chown=node:node apps/web ./apps/web
COPY --chown=node:node types ./types
USER node
CMD ["pnpm", "--dir", "apps/web", "test", "--run"]
