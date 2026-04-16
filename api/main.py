"""
API FastAPI pour servir les recommandations de films avec Spark.

Point d'entrée: uvicorn api.main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from api.config import CORS_ORIGINS, CORS_CREDENTIALS, CORS_METHODS, CORS_HEADERS
from api.routes.recommendations import router as recommendations_router
from api.startup import SparkResourceManager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gère le cycle de vie de l'application."""
    # Startup
    print("🔥 Initialisation de l'API au démarrage...")
    try:
        SparkResourceManager.get_data()
        print("✅ Données Spark pré-chargées")
    except Exception as e:
        print(f"⚠️  Erreur lors du pré-chargement Spark: {e}")
    
    try:
        SparkResourceManager.get_recommendations_df()
        print("✅ Recommandations ALS pré-chargées")
    except Exception as e:
        print(f"⚠️  Erreur lors du pré-chargement ALS: {e}")
    
    print("🎯 API prête !")
    
    yield
    
    # Shutdown
    print("🛑 Arrêt de l'API...")
    SparkResourceManager.stop()
    print("✅ Ressources libérées")


# Création de l'application FastAPI
app = FastAPI(
    title="Sparkle Movie API",
    description="API de recommandations de films basée sur le modèle ALS de Spark",
    version="1.0.0",
    lifespan=lifespan,
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=CORS_CREDENTIALS,
    allow_methods=CORS_METHODS,
    allow_headers=CORS_HEADERS,
)

# Inclure les routes
app.include_router(recommendations_router)


@app.get("/", tags=["Info"])
def home() -> dict[str, str]:
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
        }
    }


@app.get("/health", tags=["Info"])
def health_check() -> dict[str, str]:
    """Vérification de l'état de l'API."""
    return {"status": "ok", "service": "Sparkle Movie API"}
