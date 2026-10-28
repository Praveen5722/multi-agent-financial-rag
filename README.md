# Multi-Agent RAG for Financial Analysis and Risk Assessment

A TypeScript monorepo for evidence-linked financial research, using **Turborepo + pnpm**, **PostgreSQL**, and **Prisma ORM**.

## Monorepo structure

```text
apps/
  api/                 Express + TypeScript API
  web/                 React + TypeScript + Vite dashboard
packages/
  database/
    prisma/schema.prisma
    src/client.ts      Shared Prisma Client
Dockerfile
docker-compose.yml
pnpm-workspace.yaml
turbo.json
```

## Requirements

- Node.js 20+
- pnpm 9+
- Docker Desktop / Docker Engine (recommended)

## Run the full stack with Docker

```bash
docker compose up --build
```

Open:
- Dashboard: http://localhost:5173
- API health: http://localhost:8000/api/health
- PostgreSQL: localhost:5432 (database `finrag`, user `finrag`)

Compose starts PostgreSQL, synchronizes the Prisma schema for this development environment, and starts the API and frontend. The default database password is only for local development; change it before any shared deployment.

## Run locally

1. Start PostgreSQL and create a database named `finrag`.
2. Copy `.env.example` to `.env` and configure `DATABASE_URL`.
3. Install dependencies and generate Prisma Client:

```bash
pnpm install
pnpm db:generate
pnpm db:push
pnpm build
```

4. Start both applications with `pnpm dev`. The database must already be running.

## Prisma commands

```bash
pnpm db:generate   # generate typed Prisma Client
pnpm db:push       # sync schema to a development database
pnpm db:studio     # open Prisma Studio
```

For production, create and commit migrations with `prisma migrate dev`, and deploy them with `prisma migrate deploy`. Do not use `db push` as a production migration strategy.

## Current features

- PDF upload and text extraction
- PDF passages stored in PostgreSQL using Prisma
- Lexical retrieval over stored chunks
- Deterministic period-over-period metric change calculations
- Persisted analyses, evidence, calculations, risks, and agent runs
- React dashboard for uploads, analysis, agent activity, and report printing
- Docker Compose for PostgreSQL + API + frontend
- GitHub Actions typecheck/build workflow

## Current limitations

This is a starter implementation, not a complete reproduction of the research paper. Retrieval is lexical (not hybrid dense + BM25), table-aware extraction is limited, and current-news/MCP integrations and benchmark runs (FinQA, FinanceBench, T²-RAGBench, FinMRAGBench) are not implemented in the TypeScript API. The validator checks evidence coverage but cannot prove factual correctness. Verify sources and calculations before making financial decisions.

See `.env.example`. Never commit real credentials.
