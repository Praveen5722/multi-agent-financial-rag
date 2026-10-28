FROM node:20-alpine AS base
WORKDIR /workspace
RUN corepack enable
COPY package.json pnpm-workspace.yaml turbo.json tsconfig.base.json ./
COPY apps/api/package.json apps/api/package.json
COPY apps/web/package.json apps/web/package.json
COPY packages/database/package.json packages/database/package.json
RUN pnpm install
COPY . .
RUN pnpm --filter @finrag/database db:generate

FROM base AS api
EXPOSE 8000
CMD ["sh", "-c", "pnpm --filter @finrag/database db:push && pnpm --filter @finrag/api dev"]

FROM base AS web
EXPOSE 5173
CMD ["pnpm", "--filter", "@finrag/web", "dev", "--", "--host", "0.0.0.0"]
