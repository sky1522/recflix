# ==============================================
# RecFlix Development Makefile
# ==============================================
# Usage: make [target]

.PHONY: help install docker-up docker-down docker-logs db-init db-migrate backend-run frontend-run test clean

# Default target
help:
	@echo "RecFlix Development Commands"
	@echo "=============================="
	@echo ""
	@echo "Docker Commands:"
	@echo "  make docker-up       - Start all Docker services (PostgreSQL, Redis, pgAdmin)"
	@echo "  make docker-down     - Stop all Docker services"
	@echo "  make docker-logs     - View Docker logs"
	@echo "  make docker-clean    - Stop and remove all containers, volumes"
	@echo "  make docker-ps       - Show running containers"
	@echo ""
	@echo "Database Commands:"
	@echo "  make db-init         - Initialize Alembic for migrations"
	@echo "  make db-migrate      - Run database migrations"
	@echo "  make db-seed         - Seed database with movie data"
	@echo "  make db-reset        - Reset database (down + up migrations)"
	@echo ""
	@echo "Backend Commands:"
	@echo "  make backend-install - Install backend dependencies"
	@echo "  make backend-run     - Run FastAPI development server"
	@echo "  make backend-test    - Run backend tests"
	@echo ""
	@echo "Frontend Commands:"
	@echo "  make frontend-install - Install frontend dependencies"
	@echo "  make frontend-run     - Run Next.js development server"
	@echo "  make frontend-build   - Build frontend for production"
	@echo ""
	@echo "Utility Commands:"
	@echo "  make install         - Install all dependencies"
	@echo "  make dev             - Start full development environment"
	@echo "  make test            - Run all tests"
	@echo "  make clean           - Clean temporary files"
	@echo "  make env-copy        - Copy .env.example to .env"

# ==============================================
# Docker Commands
# ==============================================
docker-up:
	docker compose -f docker/docker-compose.yml up -d
	@echo ""
	@echo "Services started successfully!"
	@echo "  - PostgreSQL: localhost:5432"
	@echo "  - Redis: localhost:6379"
	@echo "  - pgAdmin: http://localhost:5050"

docker-down:
	docker compose -f docker/docker-compose.yml down

docker-logs:
	docker compose -f docker/docker-compose.yml logs -f

docker-clean:
	docker compose -f docker/docker-compose.yml down -v --remove-orphans
	@echo "All containers and volumes removed"

docker-ps:
	docker compose -f docker/docker-compose.yml ps

# ==============================================
# Database Commands
# ==============================================
db-init:
	cd backend && alembic init alembic
	@echo "Alembic initialized. Configure alembic.ini with DATABASE_URL"

db-migrate:
	cd backend && alembic upgrade head

db-migrate-create:
	cd backend && alembic revision --autogenerate -m "$(msg)"

db-seed:
	cd backend && python scripts/seed_movies.py

db-reset:
	cd backend && alembic downgrade base && alembic upgrade head

# ==============================================
# Backend Commands
# ==============================================
backend-install:
	cd backend && pip install -r requirements.txt

backend-run:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

backend-test:
	cd backend && pytest tests/ -v

backend-lint:
	cd backend && ruff check app/

backend-format:
	cd backend && ruff format app/

# ==============================================
# Frontend Commands
# ==============================================
frontend-install:
	cd frontend && npm install

frontend-run:
	cd frontend && npm run dev

frontend-build:
	cd frontend && npm run build

frontend-lint:
	cd frontend && npm run lint

# ==============================================
# Combined Commands
# ==============================================
install: backend-install frontend-install
	@echo "All dependencies installed"

dev: docker-up
	@echo ""
	@echo "Development environment ready!"
	@echo "Run 'make backend-run' and 'make frontend-run' in separate terminals"

test: backend-test
	@echo "All tests completed"

# ==============================================
# Utility Commands
# ==============================================
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleaned temporary files"

env-copy:
	cp .env.example .env
	@echo "Created .env file. Please update with your values."
