"""
Schémas Pydantic pour la validation des réponses API.

Utilisés pour la sérialisation JSON et la documentation Swagger.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class MovieRecommendation(BaseModel):
    """Schéma pour une recommandation de film."""

    movie_id: int = Field(..., description="ID du film")
    title: str = Field(..., description="Titre du film")
    predicted_rating: float = Field(..., description="Score de prédiction ALS (0-10)")
    source: str = Field("als_model", description="Source de la recommandation")


class RecommendationsResponse(BaseModel):
    """Schéma pour la liste des recommandations."""

    user_id: int = Field(..., description="ID de l'utilisateur")
    recommendations: List[MovieRecommendation] = Field(
        ..., description="Liste des films recommandés"
    )
    note: Optional[str] = Field(None, description="Note additionnelle")


class UserRating(BaseModel):
    """Schéma pour un avis utilisateur."""

    movie_id: int = Field(..., description="ID du film")
    title: str = Field(..., description="Titre du film")
    rating: float = Field(..., ge=0.5, le=5.0, description="Note donnée (0.5-5.0)")
    date: str = Field(..., description="Date de l'avis (YYYY-MM-DD)")
    timestamp: int = Field(..., description="Timestamp Unix")


class UserRatingsResponse(BaseModel):
    """Schéma pour l'historique des avis d'un utilisateur."""

    user_id: int = Field(..., description="ID de l'utilisateur")
    total_avis: int = Field(..., description="Nombre total d'avis")
    avis: List[UserRating] = Field(..., description="Liste des avis")


class Genre(BaseModel):
    """Schéma pour un genre populaire."""

    genre: str = Field(..., description="Nom du genre")
    n_ratings: int = Field(..., description="Nombre d'évaluations")


class GenresResponse(BaseModel):
    """Schéma pour la liste des genres populaires."""

    genres: List[Genre] = Field(..., description="Genres triés par popularité")


class StatisticsResponse(BaseModel):
    """Schéma pour les statistiques globales."""

    total_users: int = Field(..., description="Nombre d'utilisateurs")
    total_movies: int = Field(..., description="Nombre de films")
    total_ratings: int = Field(..., description="Nombre total d'avis")
