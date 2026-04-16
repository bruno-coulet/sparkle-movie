"""
Routes pour les recommandations de films.

Endpoints:
- GET /recommandations/{user_id}
- GET /utilisateur/{user_id}/avis
- GET /genres
- GET /statistiques
"""

from typing import Any
from fastapi import APIRouter, Query
from api.schemas import (
    RecommendationsResponse,
    UserRatingsResponse,
    GenresResponse,
    StatisticsResponse,
)
from api.services.recommendation_service import (
    RecommendationService,
    StatisticsService,
)

router = APIRouter(prefix="/api", tags=["recommendations"])


@router.get("/recommandations/{user_id}", response_model=RecommendationsResponse)
def get_recommendations(
    user_id: int,
    limit: int = Query(10, ge=1, le=100),
) -> dict[str, Any]:
    """Retourne les recommandations ALS pré-calculées pour un utilisateur.
    
    Cette endpoint utilise les prédictions ALS pré-calculées chargées en mémoire
    pour retourner instantanément les films recommandés.
    
    Paramètres:
        user_id: Identifiant de l'utilisateur (1-610)
        limit: Nombre de recommandations à retourner (défaut: 10, max: 100)
    
    Retourne:
        Liste des films recommandés par score décroissant
    """
    return RecommendationService.get_user_recommendations(user_id, limit)


@router.get("/utilisateur/{user_id}/avis", response_model=UserRatingsResponse)
def get_user_ratings(
    user_id: int,
    limit: int = Query(50, ge=1, le=100),
) -> dict[str, Any]:
    """Retourne l'historique des avis postés par un utilisateur.
    
    Paramètres:
        user_id: Identifiant de l'utilisateur
        limit: Nombre d'avis à retourner (défaut: 50, max: 100)
    
    Retourne:
        Liste des avis avec titre du film, note et date
    """
    return RecommendationService.get_user_ratings(user_id, limit)


@router.get("/genres", response_model=GenresResponse)
def get_genres_popularity() -> dict[str, Any]:
    """Retourne les genres les plus populaires selon le nombre de films.
    
    Retourne:
        Genres triés par popularité (nombre de films)
    """
    return StatisticsService.get_genres()


@router.get("/statistiques", response_model=StatisticsResponse)
def get_statistics() -> dict[str, Any]:
    """Retourne les statistiques globales sur les données.
    
    Retourne:
        Nombre d'utilisateurs, de films et d'avis
    """
    return StatisticsService.get_statistics()
