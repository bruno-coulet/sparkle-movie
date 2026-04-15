"""API FastAPI pour servir des recommandations de films avec Spark.

Entrées actuelles:
- Le module consomme les jeux de données MovieLens nettoyés au format Parquet.
- Les fichiers d'entrée sont chargés depuis data/processed:
    - ratings_clean.parquet
    - movies_clean.parquet

Contexte projet:
- Le projet inclut un notebook de modélisation ALS qui produit des recommandations.

Cible d'évolution:
- A terme, l'API doit s'appuyer sur le modèle ALS entraîné,
    ou sur un jeu de données de recommandations produit par ALS.
"""

from typing import Any
import sys
from pathlib import Path

from fastapi import FastAPI, Query
from pyspark.sql import SparkSession

# Ajouter src au chemin pour importer utils
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from utils import load_ratings_dataframe, load_movies_dataframe, top_rated_movies, most_popular_genres

# Création de l'app
app = FastAPI()

# Session Spark partagée (lazy initialization)
_spark_session: SparkSession | None = None
_ratings_df = None
_movies_df = None

def get_spark_session() -> SparkSession:
    """Crée et retourne une session Spark unique."""
    global _spark_session
    if _spark_session is None:
        _spark_session = SparkSession.builder \
            .appName("sparkle-movie-api") \
            .master("local[*]") \
            .getOrCreate()
        _spark_session.sparkContext.setLogLevel("WARN")
    return _spark_session

def get_data():
    """Charge les dataframes Spark au premier appel."""
    global _ratings_df, _movies_df
    if _ratings_df is None or _movies_df is None:
        spark = get_spark_session()
        _ratings_df = spark.read.parquet("data/processed/ratings_clean.parquet")
        _movies_df = spark.read.parquet("data/processed/movies_clean.parquet")
        # Cache les données en mémoire pour les accès rapides
        _ratings_df.cache()
        _movies_df.cache()
    return _ratings_df, _movies_df


@app.get("/")
def home() -> dict[str, str]:
    """Page d'accueil avec les endpoints disponibles."""
    return {
        "message": "Bienvenue sur l'API MovieLens Spark !",
        "endpoints": {
            "/": "Cette page",
            "/nombre_utilisateurs": "Nombre d'utilisateurs",
            "/nombre_films_notes": "Nombre de films",
            "/statistiques": "Statistiques globales",
            "/recommandations/{user_id}": "Films les mieux notés",
            "/genres": "Genres populaires",
            "/docs": "Documentation interactive (Swagger)",
        }
    }


@app.get("/recommandations/{user_id}")
def get_recommendations(
    user_id: int,
    limit: int = Query(10, ge=1, le=100),
) -> dict[str, Any]:
    """Retourne les films les mieux notés (recommandations simplifiées).

    Paramètres:
        user_id: Identifiant de l'utilisateur (non utilisé dans cette version simple)
        limit: Nombre de recommandations à retourner (défaut: 10, max: 100)
    
    Retourne:
        Un dictionnaire avec l'ID utilisateur et la liste des films recommandés
        triés par note moyenne décroissante.
    """
    ratings_df, movies_df = get_data()
    
    # Récupère les films les mieux notés
    top_movies = top_rated_movies(ratings_df, movies_df)
    
    # Convertit en Pandas et prépare la réponse
    recommendations = []
    for row in top_movies.limit(limit).collect():
        recommendations.append({
            "movie_id": int(row.movieId),
            "title": row.title,
            "avg_rating": float(row.avg_rating),
            "n_ratings": int(row.n_ratings),
        })
    
    return {"user_id": user_id, "recommendations": recommendations}

@app.get("/genres")
def get_genres_popularity() -> dict[str, Any]:
    """Retourne les genres les plus populaires selon le nombre de notes."""
    ratings_df, movies_df = get_data()
    
    # Récupère les genres populaires
    genres_df = most_popular_genres(ratings_df, movies_df)
    
    genres = []
    for row in genres_df.collect():
        genres.append({
            "genre": row.genre,
            "n_ratings": int(row.n_ratings),
        })
    
    return {"genres": genres}

@app.get("/nombre_utilisateurs")
def get_user_count() -> dict[str, Any]:
    """Retourne le nombre d'utilisateurs distincts dans les données."""
    ratings_df, _ = get_data()
    user_count = ratings_df.select("userId").distinct().count()
    return {"user_count": user_count}

@app.get("/nombre_films_notes")
def get_movie_rating_count() -> dict[str, Any]:
    """Retourne le nombre total de films notés."""
    _, movies_df = get_data()
    movie_count = movies_df.count()
    return {"movie_rating_count": movie_count}

@app.get("/statistiques")
def get_statistics() -> dict[str, Any]:
    """Retourne les statistiques globales sur les données."""
    ratings_df, movies_df = get_data()
    
    return {
        "total_users": ratings_df.select("userId").distinct().count(),
        "total_movies": movies_df.count(),
        "total_ratings": ratings_df.count(),
    }
