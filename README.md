# Multi-Agent RAG for Financial Analysis and Risk Assessment

An initial prototype inspired by the research paper *Multi-Agent Retrieval-Augmented Generation for Financial Analysis and Risk Assessment Using Deterministic Calculation and Validation*.

## Architecture

- **Supervisor agent** routes the request.
- **Document retrieval** extracts text from uploaded PDFs and retrieves relevant passages using lexical matching.
- **News agent** optionally searches current news when configured.
- **Calculator agent** performs deterministic arithmetic.
- **Synthesis agent** composes an answer with source references.
- **Validator agent** checks the response structure and evidence coverage.

## Stack

- Backend: Python, FastAPI, Pydantic
- Frontend: React, Vite
- Deployment: Docker Compose

## Run locally

```bash
docker compose up --build
```

The frontend and backend are configured in `docker-compose.yml`. For local development, install dependencies in `backend/requirements.txt` and `frontend/package.json`.

## Configuration

Copy `backend/.env.example` to `backend/.env` and configure any optional news search key if needed. Never commit secrets.

## Important limitations

This is an **initial prototype**, not a complete reproduction of the paper. Retrieval currently uses lexical matching rather than a full hybrid dense + BM25 index; MCP integration, production-grade agent orchestration, benchmark evaluation (FinQA, FinanceBench, T²-RAGBench, FinMRAGBench), and comprehensive automated tests remain future work. Validate outputs before using them for financial decisions.

## License

No license has been added yet. Do not assume the code is licensed for reuse until a license is chosen.
