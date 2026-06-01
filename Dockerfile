# =============================================================================
# Projet      : Sparkle Movie
# Fichier     : Dockerfile
# Description : Image Docker multi-stage pour l'API FastAPI + PySpark (Java 17)
# Auteur      : Sulivan Moreau
# Date        : 2026-04-19
# Version     : 1.0.0
# =============================================================================

# Stage 1 : builder — installe les dependances avec uv
FROM python:3.12-slim AS builder

RUN pip install --no-cache-dir "uv>=0.4"

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-group dev

# Stage 2 : runtime — image finale avec Java 17 (requis par PySpark)
# FROM python:3.12-slim AS runtime

# RUN apt-get update && apt-get install -y --no-install-recommends \
#         openjdk-17-jre-headless \
#         curl \
#     && rm -rf /var/lib/apt/lists/*

# ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
# ENV PATH="${JAVA_HOME}/bin:${PATH}"
# Stage 2 : runtime — image finale avec Java 21 (requis par PySpark)
FROM python:3.12-slim AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
        openjdk-21-jre-headless \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Mise à jour du chemin JAVA_HOME pour pointer vers Java 21
ENV JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
ENV PATH="${JAVA_HOME}/bin:${PATH}"

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:${PATH}"
ENV PYTHONPATH="/app"

COPY api/ ./api/
COPY src/ ./src/

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
