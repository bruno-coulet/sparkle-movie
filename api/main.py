# =============================================================================
# Projet      : Sparkle Movie
# Fichier     : api/main.py
# Description : Point d'entree FastAPI — lifespan, middleware, routes
# Auteur      : Sulivan Moreau
# Date        : 2026-04-19
# Version     : 1.0.0
# =============================================================================

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import CORS_CREDENTIALS, CORS_HEADERS, CORS_METHODS, CORS_ORIGINS, MODELS_DIR
from api.routes.recommendations import router as recommendations_router
from api.startup import SparkResourceManager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gere le cycle de vie de l'application."""
    try:
        SparkResourceManager.get_data()
    except Exception:
        pass

    try:
        SparkResourceManager.get_recommendations_df()
    except Exception:
        pass

    yield

    SparkResourceManager.stop()


app = FastAPI(
    title="Sparkle Movie API",
    description="API de recommandations de films basee sur le modele ALS de Spark",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=CORS_CREDENTIALS,
    allow_methods=CORS_METHODS,
    allow_headers=CORS_HEADERS,
)

app.include_router(recommendations_router)


@app.get("/", tags=["Info"])
def home() -> dict:
    """Page d'accueil avec les endpoints disponibles."""
    return {
        "message": "Bienvenue sur l'API Sparkle Movie !",
        "version": "1.0.0",
        "documentation": "/docs",
        "endpoints": {
            "/api/recommandations/{user_id}": "Recommandations ALS pour un utilisateur",
            "/api/utilisateur/{user_id}/avis": "Historique des avis d'un utilisateur",
            "/api/genres": "Genres populaires",
            "/api/statistiques": "Statistiques globales",
        },
    }


@app.get("/health", tags=["Info"])
def health_check() -> dict:
    """Verification de l'etat de l'API."""
    return {"status": "ok", "service": "Sparkle Movie API"}


@app.get("/metrics", tags=["Info"])
def metrics() -> dict:
    """Expose l'etat du cache Spark et des modeles charges."""
    recs_loaded = "recommendations" in SparkResourceManager._data_cache
    spark_active = SparkResourceManager._spark_session is not None

    rmse_file = Path(MODELS_DIR) / "rmse.txt"
    rmse = float(rmse_file.read_text().strip()) if rmse_file.exists() else None

    return {
        "spark_session_active": spark_active,
        "recommendations_cached": recs_loaded,
        "model_rmse": rmse,
    }
