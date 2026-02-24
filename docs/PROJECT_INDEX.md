# Project Index

This file is a quick map for navigating the RecFlix repository.

## Root

- `README.md`: setup and run guide
- `Makefile`: local development commands
- `docker-compose.yml`: top-level compose entrypoint
- `docs/`: detailed project docs
- `backend/`: FastAPI service
- `frontend/`: Next.js client
- `data/`: DB restore docs and dataset artifacts
- `scripts/`: utility scripts used across the repo

## Backend (`backend/`)

- `backend/app/main.py`: FastAPI app entrypoint
- `backend/app/api/v1/router.py`: API v1 route composition
- `backend/app/models/`: SQLAlchemy models
- `backend/app/schemas/`: Pydantic schemas
- `backend/app/services/`: integration/business services (weather, llm)
- `backend/app/core/`: DI, security, rate limiting, http client, logging config
- `backend/app/middleware/`: request ID middleware (structlog contextvars)
- `backend/tests/`: pytest test suite (conftest, auth, health, movies, recommendations)
- `backend/alembic/`: DB migrations (Alembic)
- `backend/scripts/`: migration/data maintenance scripts
- `backend/scripts/README.md`: scripts documentation (16 scripts)

## Frontend (`frontend/`)

- `frontend/app/`: Next.js App Router pages/layouts
- `frontend/components/`: reusable UI and feature components
- `frontend/lib/`: API client and utility modules
- `frontend/hooks/`: custom React hooks
- `frontend/stores/`: Zustand stores
- `frontend/types/`: shared TypeScript types

## Documentation (`docs/`)

- `docs/ARCHITECTURE.md`: system architecture (data flow, cache, auth, CI/CD)
- `docs/RECOMMENDATION_LOGIC.md`: recommendation scoring details
- `docs/HANDOFF_CONTEXT.md`: project handoff context (Phase 50 기준)
- `docs/PROJECT_INDEX.md`: this file — project file index
- `docs/DATA_PREPROCESSING.md`: data prep flow
- `docs/PROJECT_REVIEW.md`: project review and roadmap
- `docs/devlog/`: implementation logs
- `docs/eda/`: exploratory analysis scripts/results

## Cleanup Rules

- Run `make clean` for local cleanup.
- Run `make clean-dry-run` to preview what will be deleted.
- Generated artifacts like `*.tsbuildinfo` are ignored by git.
