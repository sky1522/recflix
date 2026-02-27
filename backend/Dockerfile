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

# Download v2.0 ML model files (Two-Tower + LightGBM)
RUN mkdir -p backend/data/models/two_tower backend/data/models/reranker && \
    curl -fSL -o backend/data/models/two_tower/model_v1.pt \
    "https://media.githubusercontent.com/media/sky1522/recflix/main/backend/data/models/two_tower/model_v1.pt" && \
    echo "55b024c2aaf8a24e326a8e4c2e2dd25e461de5269221dc02b56ab7de6d17e539  backend/data/models/two_tower/model_v1.pt" | sha256sum -c - && \
    curl -fSL -o backend/data/models/two_tower/faiss_index.bin \
    "https://media.githubusercontent.com/media/sky1522/recflix/main/backend/data/models/two_tower/faiss_index.bin" && \
    echo "d09001c3b779ef8123c889bc7120b9b22e69dadc15b922c5063621a593d7f09e  backend/data/models/two_tower/faiss_index.bin" | sha256sum -c - && \
    curl -fSL -o backend/data/models/two_tower/item_embeddings_tt.npy \
    "https://media.githubusercontent.com/media/sky1522/recflix/main/backend/data/models/two_tower/item_embeddings_tt.npy" && \
    echo "861274d2c8d74809886f86d1f4bf89ff4a91ff1ab125a1cd78143049d1df654d  backend/data/models/two_tower/item_embeddings_tt.npy" | sha256sum -c - && \
    curl -fSL -o backend/data/models/two_tower/movie_id_map.json \
    "https://raw.githubusercontent.com/sky1522/recflix/main/backend/data/models/two_tower/movie_id_map.json" && \
    echo "261c66e073e63688657c76c350402a47754085631442e8d1be088c58242c204e  backend/data/models/two_tower/movie_id_map.json" | sha256sum -c - && \
    curl -fSL -o backend/data/models/reranker/lgbm_v1.txt \
    "https://media.githubusercontent.com/media/sky1522/recflix/main/backend/data/models/reranker/lgbm_v1.txt" && \
    echo "37e896e3b2083ffee17877e2aa796831c6ef7424952bdc71da722303f0438ed7  backend/data/models/reranker/lgbm_v1.txt" | sha256sum -c -

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
