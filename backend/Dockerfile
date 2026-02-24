# RecFlix Backend Dockerfile
# Build context: repo root (via railway.toml dockerfilePath)
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application code only
COPY backend/ ./backend/

# Download large data files from GitHub LFS (not included in upload)
# SHA256 checksums verified to detect corrupted or tampered downloads
RUN mkdir -p backend/data/movielens backend/data/embeddings && \
    curl -fSL -o backend/data/movielens/svd_model.pkl \
    "https://media.githubusercontent.com/media/sky1522/recflix/main/backend/data/movielens/svd_model.pkl" && \
    echo "343853948b2e848dbba26d193fd5e3923df02a217a0c19649bd27d0ad8f353b5  backend/data/movielens/svd_model.pkl" | sha256sum -c - && \
    curl -fSL -o backend/data/embeddings/movie_embeddings.npy \
    "https://media.githubusercontent.com/media/sky1522/recflix/main/backend/data/embeddings/movie_embeddings.npy" && \
    echo "e76cb82509c1be887269548642c9cd8625206e641c10b47e2e53b33f88a3fcd6  backend/data/embeddings/movie_embeddings.npy" | sha256sum -c - && \
    curl -fSL -o backend/data/embeddings/embedding_metadata.json \
    "https://raw.githubusercontent.com/sky1522/recflix/main/backend/data/embeddings/embedding_metadata.json" && \
    echo "767501ded5a0426e629648ab00e3f981d5f3728715ed193a37ebf1b67345afd7  backend/data/embeddings/embedding_metadata.json" | sha256sum -c - && \
    curl -fSL -o backend/data/embeddings/movie_id_index.json \
    "https://raw.githubusercontent.com/sky1522/recflix/main/backend/data/embeddings/movie_id_index.json" && \
    echo "6c248d08dcc1ed14b0fd9c7eb3a35bc415da538c383926501b7af59e692658ee  backend/data/embeddings/movie_id_index.json" | sha256sum -c -

# Create non-root user for security
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Start the application
WORKDIR /app/backend
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
