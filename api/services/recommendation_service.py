"""
Service de recommandations.

Logique métier pour les recommandations et statistiques utilisateur.
"""

from typing import Any
from datetime import datetime
import pandas as pd
from pyspark.sql.functions import col, desc

from api.startup import SparkResourceManager


class RecommendationService:
    """Service pour les recommandations et avis utilisateur."""
    
    @staticmethod
    def get_user_recommendations(user_id: int, limit: int = 10) -> dict[str, Any]:
        """Retourne les recommandations ALS pré-calculées pour un utilisateur.
        
        Paramètres:
            user_id: Identifiant de l'utilisateur (1-610)
            limit: Nombre de recommandations à retourner
        
        Retourne:
            Dictionnaire avec l'ID utilisateur et les films recommandés
        """
        recommendations_df = SparkResourceManager.get_recommendations_df()
        
        if recommendations_df is None or recommendations_df.empty:
            return {
                "user_id": user_id,
                "recommendations": [],
                "note": "Recommandations ALS non disponibles"
            }
        
        # Filtrer par utilisateur
        user_recs = recommendations_df[recommendations_df["userId"] == user_id]
        
        if user_recs.empty:
            return {
                "user_id": user_id,
                "recommendations": [],
                "note": f"Aucune recommandation trouvée pour l'utilisateur {user_id}"
            }
        
        # Trier par score et limiter
        user_recs = user_recs.sort_values("predicted_rating", ascending=False).head(limit)
        
        # Convertir en résultat
        recommendations = []
        for _, row in user_recs.iterrows():
            recommendations.append({
                "movie_id": int(row["movieId"]),
                "title": row["title"],
                "predicted_rating": float(row["predicted_rating"]),
                "source": "als_model",
            })
        
        return {"user_id": user_id, "recommendations": recommendations}
    
    @staticmethod
    def get_user_ratings(user_id: int, limit: int = 50) -> dict[str, Any]:
        """Retourne l'historique des avis d'un utilisateur.
        
        Paramètres:
            user_id: Identifiant de l'utilisateur
            limit: Nombre d'avis à retourner
        
        Retourne:
            Dictionnaire avec liste des avis utilisateur
        """
        ratings_df, movies_df = SparkResourceManager.get_data()
        
        # Filtrer par utilisateur et joindre avec les films
        user_avis = ratings_df.filter(
            col("userId") == user_id
        ).join(
            movies_df.select("movieId", "title"),
            on="movieId",
            how="left"
        ).select(
            col("movieId"),
            col("title"),
            col("rating"),
            col("timestamp")
        ).orderBy(
            desc("timestamp")
        ).limit(limit)
        
        # Convertir en résultat
        avis = []
        for row in user_avis.collect():
            date_avis = datetime.fromtimestamp(int(row.timestamp)).strftime("%Y-%m-%d")
            
            avis.append({
                "movie_id": int(row.movieId),
                "title": row.title,
                "rating": float(row.rating),
                "date": date_avis,
                "timestamp": int(row.timestamp),
            })
        
        return {
            "user_id": user_id,
            "total_avis": len(avis),
            "avis": avis
        }


class StatisticsService:
    """Service pour les statistiques globales."""
    
    @staticmethod
    def get_statistics() -> dict[str, Any]:
        """Retourne les statistiques globales sur les données."""
        ratings_df, movies_df = SparkResourceManager.get_data()
        
        return {
            "total_users": ratings_df.select("userId").distinct().count(),
            "total_movies": movies_df.count(),
            "total_ratings": ratings_df.count(),
        }
    
    @staticmethod
    def get_genres() -> dict[str, list]:
        """Retourne les genres les plus populaires."""
        from pyspark.sql.functions import explode, split
        
        _, movies_df = SparkResourceManager.get_data()
        
        # Explode les genres et les compte
        genres_raw = movies_df.select(
            explode(split(col("genres"), r"\|")).alias("genre")
        ).groupBy("genre").count().orderBy(desc("count"))
        
        genres = []
        for row in genres_raw.collect():
            genres.append({
                "genre": row.genre,
                "n_ratings": int(row["count"]),
            })
        
        return {"genres": genres}
