"""
Module d'ingestion Spark pour MovieLens (version small).
- Charge ratings.csv et movies.csv en DataFrames Spark
- Nettoie les données (NA, doublons)
- Analyse les tendances (top films, genres populaires)
- Génère des visualisations Python

- main charge ratings et movies avec schemas explicites, puis montre une jointure de verification.
"""

from typing import Literal, Tuple
from pathlib import Path

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import avg, col, count, desc, explode, split
from pyspark.sql.types import FloatType, IntegerType, LongType, StringType, StructField, StructType

DataSource = Literal["raw_small", "raw_big", "processed_small", "processed_big"]

def get_project_root() -> Path:
    """Retourne la racine du projet, peu importe d'où le code est lancé."""
    # __file__ est le chemin de utils.py, .parent est src/, .parent.parent est la racine
    return Path(__file__).resolve().parent.parent

def create_spark_session() -> SparkSession:
    """Cree et retourne une session Spark locale."""
    return (
        SparkSession.builder.appName("MovieLens")
        # Détermine combien de coeurs CPU utiliser pour l'exécution locale.
        .master("local[*]")
        # permet de réutiliser une session existante si elle est déjà créée, ou d’en créer une nouvelle sinon.
        .getOrCreate()
    )

def resolve_data_source_paths(
    source: DataSource,
    project_root: Path | None = None,
) -> tuple[str, Path, Path]:
    """Résout le format et les chemins ratings/movies selon la source demandée."""
    root = project_root or get_project_root()
    data_root = root / "data"

    sources: dict[DataSource, tuple[str, Path, Path]] = {
        "raw_small": (
            "csv",
            data_root / "raw_small" / "ratings.csv",
            data_root / "raw_small" / "movies.csv",
        ),
        "raw_big": (
            "csv",
            data_root / "raw_big" / "ratings.csv",
            data_root / "raw_big" / "movies.csv",
        ),
        "processed_small": (
            "parquet",
            data_root / "processed" / "small" / "ratings_clean.parquet",
            data_root / "processed" / "small" / "movies_clean.parquet",
        ),
        "processed_big": (
            "parquet",
            data_root / "processed" / "big" / "ratings_clean.parquet",
            data_root / "processed" / "big" / "movies_clean.parquet",
        ),
    }

    dataset_format, path_ratings, path_movies = sources[source]
    if not path_ratings.exists() or not path_movies.exists():
        raise FileNotFoundError(
            f"Fichiers introuvables pour source={source}: {path_ratings} | {path_movies}"
        )

    return dataset_format, path_ratings, path_movies

def load_data_source(
    spark: SparkSession,
    source: DataSource,
    project_root: Path | None = None,
) -> tuple[DataFrame, DataFrame, str, Path, Path]:
    """Charge ratings/movies selon la source et retourne DataFrames + métadonnées."""
    dataset_format, path_ratings, path_movies = resolve_data_source_paths(
        source, project_root=project_root
    )

    if dataset_format == "csv":
        df_ratings = load_ratings_dataframe(spark, path_ratings.as_posix())
        df_movies = load_movies_dataframe(spark, path_movies.as_posix())
    else:
        df_ratings = spark.read.parquet(path_ratings.as_posix())
        df_movies = spark.read.parquet(path_movies.as_posix())

    return df_ratings, df_movies, dataset_format, path_ratings, path_movies

def load_ratings_dataframe(spark: SparkSession, relative_path: str) -> DataFrame:
    """Charge ratings.csv avec un schéma explicite.
       Version robuste pour macOS / WSL / Windows.
    """
    # Accepte un chemin relatif au projet ou un chemin absolu.
    path_candidate = Path(relative_path)
    if path_candidate.is_absolute():
        path_objet = path_candidate.resolve()
    else:
        path_objet = (get_project_root() / path_candidate).resolve()

    # 2. Vérification de sécurité (Python vérifie si le fichier est là)
    if not path_objet.exists():
        raise FileNotFoundError(f"Fichier introuvable : {path_objet}")

    # 3. Définition du schéma
    ratings_schema = StructType([
        StructField("userId", IntegerType(), True),
        StructField("movieId", IntegerType(), True),
        StructField("rating", FloatType(), True),
        StructField("timestamp", LongType(), True),
    ])

    # 4. Conversion en STRING pour Spark
    # Sur Mac, on force le format string simple du chemin absolu
    path_final = str(path_objet)

    return (
        spark.read.format("csv")
        .option("header", "true")
        .option("sep", ",")
        .schema(ratings_schema)
        .load(path_final) # Spark prend la string ici
    )


def load_movies_dataframe(spark: SparkSession, csv_path: str) -> DataFrame:
    """Charge movies.csv avec un schema explicite."""
    movies_schema = StructType(
        [
            StructField("movieId", IntegerType(), True),
            StructField("title", StringType(), True),
            StructField("genres", StringType(), True),
        ]
    )

    return (
        spark.read.options(header=True, sep=",")
        .schema(movies_schema)
        .csv(csv_path)
    )

def load_dataframes(spark: SparkSession) -> Tuple[DataFrame, DataFrame]:
    """Charge ratings.csv et movies.csv avec schémas explicites."""
    ratings_schema = StructType(
        [
            StructField("userId", IntegerType(), True),
            StructField("movieId", IntegerType(), True),
            StructField("rating", FloatType(), True),
            StructField("timestamp", LongType(), True),
        ]
    )

    movies_schema = StructType(
        [
            StructField("movieId", IntegerType(), True),
            StructField("title", StringType(), True),
            StructField("genres", StringType(), True),
        ]
    )

    df_ratings = (
        spark.read.options(header=True, sep=",")
        .schema(ratings_schema)
        .csv("data/raw_small/ratings.csv")
    )

    df_movies = (
        spark.read.options(header=True, sep=",")
        .schema(movies_schema)
        .csv("data/raw_small/movies.csv")
    )

    return df_ratings, df_movies

def clean_data(df_ratings: DataFrame, df_movies: DataFrame) -> Tuple[DataFrame, DataFrame]:
    """Nettoie les DataFrames: valeurs manquantes, doublons et qualité minimale."""
    # Ratings: retire NA sur colonnes critiques
    df_ratings_clean = df_ratings.dropna(subset=["userId", "movieId", "rating"])

    # Retire doublons exacts
    df_ratings_clean = df_ratings_clean.dropDuplicates()

    # Optionnel: garde seulement les notes valides [0.5, 5.0]
    df_ratings_clean = df_ratings_clean.filter((col("rating") >= 0.5) & (col("rating") <= 5.0))

    # Movies: retire NA sur identifiants et titre
    df_movies_clean = df_movies.dropna(subset=["movieId", "title"]).dropDuplicates(["movieId"])

    return df_ratings_clean, df_movies_clean

def preview_data(df_ratings: DataFrame, df_movies: DataFrame) -> None:
    """Affiche la structure et 10 lignes de chaque DataFrame."""
    print("\n--- Ratings ---")
    df_ratings.printSchema()
    df_ratings.show(10, truncate=False)

    print("\n--- Movies ---")
    df_movies.printSchema()
    df_movies.show(10, truncate=False)

def top_rated_movies(df_ratings: DataFrame, df_movies: DataFrame) -> DataFrame:
    """Retourne les films les mieux notés avec un seuil minimal de votes.
     pour éviter les films notés 5/5 avec une seule note
     """
    df_join = df_ratings.join(df_movies, on="movieId", how="inner")

    df_top = (
        df_join.groupBy("movieId", "title")
        .agg(
            avg("rating").alias("avg_rating"),
            count("rating").alias("n_ratings"),
        )
        .filter(col("n_ratings") >= 50)
        .orderBy(desc("avg_rating"), desc("n_ratings"))
    )

    return df_top

def most_popular_genres(df_ratings: DataFrame, df_movies: DataFrame) -> DataFrame:
    """Calcule les genres les plus populaires selon le nombre de notes.
       “explose” la colonne genres (séparée par |) pour compter genre par genre.
    """
    df_join = df_ratings.join(df_movies, on="movieId", how="inner")

    df_genres = (
        df_join.withColumn("genre", explode(split(col("genres"), "\\|")))
        .groupBy("genre")
        .agg(count("*").alias("n_ratings"))
        .orderBy(desc("n_ratings"))
    )

    return df_genres

def plot_results(df_top_movies: DataFrame, df_top_genres: DataFrame) -> None:
    """Génère des visualisations avec matplotlib/seaborn
    Idée clé :
    faire les agrégations avec Spark
    puis convertir seulement le top N en Pandas pour tracer vite.
    """
    import matplotlib.pyplot as plt
    import seaborn as sns

    sns.set_theme(style="whitegrid")

    # Top 10 films
    pdf_movies = df_top_movies.limit(10).toPandas()

    plt.figure(figsize=(12, 6))
    sns.barplot(data=pdf_movies, x="avg_rating", y="title")
    plt.title("Top 10 films (note moyenne, min 50 votes)")
    plt.xlabel("Note moyenne")
    plt.ylabel("Film")
    plt.tight_layout()
    plt.show()

    # Top 10 genres
    pdf_genres = df_top_genres.limit(10).toPandas()

    plt.figure(figsize=(10, 5))
    sns.barplot(data=pdf_genres, x="n_ratings", y="genre")
    plt.title("Top 10 genres les plus populaires")
    plt.xlabel("Nombre de notes")
    plt.ylabel("Genre")
    plt.tight_layout()
    plt.show()


def test_session_join() -> None:
    """Point d'entree: charge les CSV et cree les DataFrames Spark."""
    spark = create_spark_session()

    path_ratings = "data/raw_small/ratings.csv"
    path_movies = "data/raw_small/movies.csv"

    try:
        df_ratings = load_ratings_dataframe(spark, path_ratings)
        df_movies = load_movies_dataframe(spark, path_movies)

        print("--- DataFrame ratings ---")
        df_ratings.printSchema()
        print(f"Lignes ratings: {df_ratings.count()}")
        df_ratings.show(5, truncate=False)

        print("\n--- DataFrame movies ---")
        df_movies.printSchema()
        print(f"Lignes movies: {df_movies.count()}")
        df_movies.show(5, truncate=False)

        # Verification metier: associer chaque note au titre du film.
        df_ratings_movies = df_ratings.join(df_movies, on="movieId", how="inner")
        print("\n--- Jointure ratings x movies ---")
        df_ratings_movies.select("userId", "movieId", "title", "rating").show(10, truncate=False)

        df_ratings.write.mode("overwrite").parquet("data/processed/ratings_clean.parquet")
        df_movies.write.mode("overwrite").parquet("data/processed/movies_clean.parquet")

        print("\nImport terminee avec succes.")
    except Exception as exc:
        print(f"Erreur lors de l'import: {exc}")
    finally:
        spark.stop()

def main() -> None:
    """Exécute le pipeline complet d'import, nettoyage, analyse et visualisation."""
    spark = create_spark_session()
    try:
        df_ratings, df_movies = load_dataframes(spark)
        preview_data(df_ratings, df_movies)

        df_ratings_clean, df_movies_clean = clean_data(df_ratings, df_movies)

        df_top_movies = top_rated_movies(df_ratings_clean, df_movies_clean)
        df_top_genres = most_popular_genres(df_ratings_clean, df_movies_clean)

        print("\n--- Top films ---")
        df_top_movies.show(10, truncate=False)

        print("\n--- Genres populaires ---")
        df_top_genres.show(10, truncate=False)

        plot_results(df_top_movies, df_top_genres)

    finally:
        spark.stop()



if __name__ == "__main__":
    main()