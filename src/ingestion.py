"""
Module d'ingestion Spark pour MovieLens (version small).
Ce script charge ratings.csv et movies.csv en DataFrames Spark
avec schemas explicites, puis montre une jointure de verification.
"""

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.types import FloatType, IntegerType, LongType, StringType, StructField, StructType


def create_spark_session() -> SparkSession:
    """Cree et retourne une session Spark locale."""
    return (
        SparkSession.builder
        .appName("MovieLens")
        .master("local[*]")
        # permet de réutiliser une session existante si elle est déjà créée, ou d’en créer une nouvelle sinon.
        .getOrCreate()
    )


def load_ratings_dataframe(spark: SparkSession, csv_path: str) -> DataFrame:
    """Charge ratings.csv avec un schema explicite."""
    ratings_schema = StructType(
        [
            StructField("userId", IntegerType(), True),
            StructField("movieId", IntegerType(), True),
            StructField("rating", FloatType(), True),
            StructField("timestamp", LongType(), True),
        ]
    )

    return (
        spark.read.options(header=True, sep=",")
        .schema(ratings_schema)
        .csv(csv_path)
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


def main() -> None:
    """Point d'entree: charge les CSV et cree les DataFrames Spark."""
    spark = create_spark_session()

    path_ratings = "data/raw/small/ratings.csv"
    path_movies = "data/raw/small/movies.csv"

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

        print("\nIngestion terminee avec succes.")
    except Exception as exc:
        print(f"Erreur lors de l'ingestion: {exc}")
    finally:
        spark.stop()


if __name__ == "__main__":
    main()