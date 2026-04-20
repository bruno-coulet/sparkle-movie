# =============================================================================
# Projet      : Sparkle Movie
# Fichier     : src/train.py
# Description : Entraine le modele ALS, evalue le RMSE et genere recommendations
# Auteur      : Sulivan Moreau
# Date        : 2026-04-19
# Version     : 1.0.0
# =============================================================================

import logging
import os
import shutil
import time
from pathlib import Path

from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml.recommendation import ALS
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, explode

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

RMSE_THRESHOLD = 1.2


def train_als() -> None:
    """Entraine le modele ALS, sauvegarde recommendations.csv et rmse.txt."""

    project_root = Path(__file__).parent.parent
    data_processed = project_root / "data" / "processed"
    models_dir = project_root / "models"
    models_dir.mkdir(parents=True, exist_ok=True)

    spark = (
        SparkSession.builder.appName("ALSTraining")
        .master("local[*]")
        .config("spark.driver.memory", "4g")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")

    logger.info("Entraînement du modele ALS")
    logger.info("=" * 70)
    start_time = time.time()

    # =========================================================================
    # ETAPE 1 : Charger les donnees
    # =========================================================================
    ratings_path = data_processed / "ratings_clean.parquet"
    movies_path = data_processed / "movies_clean.parquet"

    if not ratings_path.exists() or not movies_path.exists():
        logger.error("Fichiers Parquet absents — executez d'abord src/preprocess.py")
        spark.stop()
        return

    ratings_df = spark.read.parquet(str(ratings_path))
    movies_df = spark.read.parquet(str(movies_path))
    logger.info("%d evaluations, %d films charges", ratings_df.count(), movies_df.count())

    # =========================================================================
    # ETAPE 2 : Split train / test (80/20) et entraine ALS
    # =========================================================================
    train_df, test_df = ratings_df.randomSplit([0.8, 0.2], seed=42)

    als = ALS(
        maxIter=10,
        regParam=0.01,
        userCol="userId",
        itemCol="movieId",
        ratingCol="rating",
        coldStartStrategy="drop",
        nonnegative=True,
        seed=42,
    )

    logger.info("Entraine ALS sur le split train...")
    als_model = als.fit(train_df)
    logger.info("Modele ALS entraine")

    # =========================================================================
    # ETAPE 3 : Evaluer le RMSE sur le set de test
    # =========================================================================
    predictions = als_model.transform(test_df)
    evaluator = RegressionEvaluator(
        metricName="rmse", labelCol="rating", predictionCol="prediction"
    )
    rmse = evaluator.evaluate(predictions)
    logger.info("RMSE sur le set de test : %.4f", rmse)

    rmse_file = models_dir / "rmse.txt"
    rmse_file.write_text(f"{rmse:.4f}")
    logger.info("RMSE sauvegarde dans %s", rmse_file)

    if rmse >= RMSE_THRESHOLD:
        logger.warning(
            "RMSE %.4f >= seuil %.1f — le build CI echouera. Ajustez les hyperparametres.",
            rmse,
            RMSE_THRESHOLD,
        )

    # =========================================================================
    # ETAPE 4 : Generer les recommandations sur l'ensemble des utilisateurs
    # =========================================================================
    logger.info("Generation des recommandations (top 50 par utilisateur)...")

    # Re-entraine sur toutes les donnees pour les recommandations finales
    als_model_full = als.fit(ratings_df)

    user_ids = ratings_df.select("userId").distinct()
    recommendations_df = als_model_full.recommendForUserSubset(user_ids, 50)

    recommendations_exploded = recommendations_df.select(
        col("userId"),
        explode(col("recommendations")).alias("rec"),
    ).select(
        col("userId"),
        col("rec.movieId"),
        col("rec.rating").alias("predicted_rating"),
    )

    recommendations_with_titles = recommendations_exploded.join(
        movies_df.select("movieId", "title"),
        on="movieId",
        how="left",
    ).select("userId", "movieId", "title", "predicted_rating")

    logger.info("%d recommandations generees", recommendations_with_titles.count())

    # =========================================================================
    # ETAPE 5 : Sauvegarder
    # =========================================================================
    reco_parquet = models_dir / "recommendations.parquet"
    recommendations_with_titles.write.mode("overwrite").parquet(str(reco_parquet))
    logger.info("Recommandations Parquet : %s", reco_parquet)

    reco_csv_dir = models_dir / "recommendations_csv_tmp"
    recommendations_with_titles.coalesce(1).write.option("header", "true").mode("overwrite").csv(
        str(reco_csv_dir)
    )

    csv_files = [f for f in os.listdir(str(reco_csv_dir)) if f.endswith(".csv")]
    if csv_files:
        shutil.move(str(reco_csv_dir / csv_files[0]), str(models_dir / "recommendations.csv"))
        shutil.rmtree(str(reco_csv_dir))
        logger.info("Recommandations CSV : %s", models_dir / "recommendations.csv")
    else:
        logger.warning("Aucun fichier CSV genere")

    elapsed = time.time() - start_time
    logger.info("=" * 70)
    logger.info("Entraînement termine en %.1f secondes", elapsed)
    logger.info("RMSE final : %.4f (seuil : %.1f)", rmse, RMSE_THRESHOLD)
    logger.info("=" * 70)

    spark.stop()


if __name__ == "__main__":
    train_als()
