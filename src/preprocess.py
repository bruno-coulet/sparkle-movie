"""
Préparation des données MovieLens.

Convertit les fichiers CSV en Parquet pour optimiser les accès avec Spark.

Utilisation: python src/preprocess.py
"""

from pathlib import Path

from pyspark.sql import SparkSession


def prepare_data():
    """Convertit les données CSV en Parquet."""
    # Chemins
    project_root = Path(__file__).parent.parent
    data_raw = project_root / "data"
    data_processed = project_root / "data" / "processed"

    data_processed.mkdir(parents=True, exist_ok=True)

    # Créer une session Spark
    spark = SparkSession.builder.appName("DataPreparation").master("local[*]").getOrCreate()

    spark.sparkContext.setLogLevel("WARN")

    print("📊 Conversion des données CSV → Parquet...")
    print("=" * 60)

    # Traiter ratings.csv
    print("📥 Chargement de ratings.csv...")
    ratings_csv = data_raw / "ratings.csv"
    if ratings_csv.exists():
        ratings_df = (
            spark.read.option("header", "true").option("inferSchema", "true").csv(str(ratings_csv))
        )

        ratings_parquet = data_processed / "ratings_clean.parquet"
        ratings_df.write.mode("overwrite").parquet(str(ratings_parquet))
        print(f"✅ ratings_clean.parquet créé ({ratings_df.count():,} lignes)")
    else:
        print(f"❌ {ratings_csv} introuvable!")

    # Traiter movies.csv
    print("📥 Chargement de movies.csv...")
    movies_csv = data_raw / "movies.csv"
    if movies_csv.exists():
        movies_df = (
            spark.read.option("header", "true").option("inferSchema", "true").csv(str(movies_csv))
        )

        movies_parquet = data_processed / "movies_clean.parquet"
        movies_df.write.mode("overwrite").parquet(str(movies_parquet))
        print(f"✅ movies_clean.parquet créé ({movies_df.count():,} lignes)")
    else:
        print(f"❌ {movies_csv} introuvable!")

    print("=" * 60)
    print("✨ Préparation des données terminée !")
    print(f"📁 Fichiers créés dans: {data_processed}")

    spark.stop()


if __name__ == "__main__":
    prepare_data()
