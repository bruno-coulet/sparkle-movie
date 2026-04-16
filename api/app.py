"""API FastAPI pour servir des recommandations de films avec Spark.

L'API charge:
- le modèle ALS Spark sauvegardé dans ``models/als_model`` pour les recommandations;
- les jeux de données MovieLens nettoyés au format Parquet pour les statistiques et le repli.

Objectif:
- fournir une API de recommandation personnalisée adaptée à un gros volume de données.
"""

from typing import Any
import sys
from pathlib import Path

from fastapi import FastAPI, Query
from pyspark.ml.recommendation import ALSModel
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

# Ajouter src au chemin pour importer utils
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from utils import get_project_root, most_popular_genres, top_rated_movies

# Création de l'app
app = FastAPI()

# Session Spark partagée (lazy initialization)
_spark_session: SparkSession | None = None
_ratings_df = None
_movies_df = None
_als_model: ALSModel | None = None

PROJECT_ROOT = get_project_root()
MODELS_DIR = PROJECT_ROOT / "models" / "als_model"
PROCESSED_ROOT = PROJECT_ROOT / "data" / "processed" / "small"


def get_spark_session() -> SparkSession:
    """Crée et retourne une session Spark unique."""
    global _spark_session
    if _spark_session is None:
        _spark_session = (
            SparkSession.builder.appName("sparkle-movie-api").master("local[*]").getOrCreate()
        )
        _spark_session.sparkContext.setLogLevel("WARN")
    return _spark_session


def get_als_model() -> ALSModel:
    """Charge et met en cache le modèle ALS sauvegardé."""
    global _als_model
    if _als_model is None:
        if not MODELS_DIR.exists():
            raise FileNotFoundError(
                f"Modèle ALS introuvable: {MODELS_DIR}. Exécute d'abord le notebook de modélisation."
            )
        _als_model = ALSModel.load(str(MODELS_DIR))
    return _als_model


def get_movies_data():
    """Charge le DataFrame des films nettoyés au premier appel."""
    global _movies_df
    if _movies_df is None:
        spark = get_spark_session()
        movies_path = PROCESSED_ROOT / "movies_clean.parquet"
        if not movies_path.exists():
            raise FileNotFoundError(f"Fichier introuvable: {movies_path}")
        _movies_df = spark.read.parquet(movies_path.as_posix()).cache()
    return _movies_df


def get_ratings_data():
    """Charge le DataFrame des notes nettoyées uniquement si nécessaire."""
    global _ratings_df
    if _ratings_df is None:
        spark = get_spark_session()
        ratings_path = PROCESSED_ROOT / "ratings_clean.parquet"
        if not ratings_path.exists():
            raise FileNotFoundError(f"Fichier introuvable: {ratings_path}")
        _ratings_df = spark.read.parquet(ratings_path.as_posix()).cache()
    return _ratings_df


def build_fallback_recommendations(limit: int) -> list[dict[str, Any]]:
    """Construit une liste de repli basée sur les films les mieux notés."""
    ratings_df = get_ratings_data()
    movies_df = get_movies_data()
    top_movies = top_rated_movies(ratings_df, movies_df).limit(limit)

    return [
        {
            "movie_id": int(row.movieId),
            "title": row.title,
            "score": float(row.avg_rating),
            "n_ratings": int(row.n_ratings),
            "source": "fallback_top_rated",
        }
        for row in top_movies.collect()
    ]


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
            "/recommandations/{user_id}": "Recommandations personnalisées ALS",
            "/genres": "Genres populaires",
            "/docs": "Documentation interactive (Swagger)",
        }
    }


@app.get("/recommandations/{user_id}")
def get_recommendations(
    user_id: int,
    limit: int = Query(10, ge=1, le=100),
) -> dict[str, Any]:
    """Retourne des recommandations personnalisées à partir du modèle ALS.

    Paramètres:
        user_id: Identifiant de l'utilisateur
        limit: Nombre de recommandations à retourner (défaut: 10, max: 100)

    Retourne:
        Un dictionnaire avec l'ID utilisateur, la source utilisée et la liste des films recommandés.
    """
    model = get_als_model()
    movies_df = get_movies_data()
    spark = get_spark_session()

    user_subset = spark.createDataFrame([(user_id,)], ["userId"])
    recommendation_df = model.recommendForUserSubset(user_subset, limit)

    joined_df = (
        recommendation_df.select(
            "userId",
            F.explode("recommendations").alias("recommendation"),
        )
        .select(
            F.col("userId"),
            F.col("recommendation.movieId").alias("movieId"),
            F.col("recommendation.rating").alias("score"),
        )
        .join(movies_df.select("movieId", "title"), on="movieId", how="left")
        .orderBy(F.desc("score"))
    )

    recommendations = [
        {
            "movie_id": int(row.movieId),
            "title": row.title,
            "score": float(row.score),
            "source": "als_model",
        }
        for row in joined_df.collect()
    ]

    if not recommendations:
        return {
            "user_id": user_id,
            "source": "fallback_top_rated",
            "recommendations": build_fallback_recommendations(limit),
        }

    return {"user_id": user_id, "source": "als_model", "recommendations": recommendations}


@app.get("/genres")
def get_genres_popularity() -> dict[str, Any]:
    """Retourne les genres les plus populaires selon le nombre de notes."""
    ratings_df = get_ratings_data()
    movies_df = get_movies_data()

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
    ratings_df = get_ratings_data()
    user_count = ratings_df.select("userId").distinct().count()
    return {"user_count": user_count}


@app.get("/nombre_films_notes")
def get_movie_rating_count() -> dict[str, Any]:
    """Retourne le nombre total de films notés."""
    ratings_df = get_ratings_data()
    movie_count = ratings_df.select("movieId").distinct().count()
    return {"movie_count": movie_count}


@app.get("/statistiques")
def get_statistics() -> dict[str, Any]:
    """Retourne les statistiques globales sur les données."""
    ratings_df = get_ratings_data()
    movies_df = get_movies_data()

    return {
        "total_users": ratings_df.select("userId").distinct().count(),
        "total_movies": movies_df.count(),
        "total_ratings": ratings_df.count(),
    }
