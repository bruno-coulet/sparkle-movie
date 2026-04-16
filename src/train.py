"""
Entraînement du modèle ALS et génération des recommandations.

Crée une matrice pré-calculée de 50 recommandations par utilisateur
pour que l'API les récupère instantanément sans calculs lourds.

Utilisation: python src/train.py
"""

from pathlib import Path
import time
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, explode
from pyspark.ml.recommendation import ALS


def train_als():
    """Entraîne le modèle ALS et génère les recommandations."""
    
    # Chemins
    project_root = Path(__file__).parent.parent
    data_processed = project_root / "data" / "processed"
    models_dir = project_root / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    
    # Créer une session Spark
    spark = SparkSession.builder \
        .appName("ALSTraining") \
        .master("local[*]") \
        .config("spark.driver.memory", "4g") \
        .getOrCreate()
    
    spark.sparkContext.setLogLevel("WARN")
    
    print("🤖 Entraînement du modèle ALS...")
    print("=" * 70)
    
    start_time = time.time()
    
    # ========================================================================
    # ÉTAPE 1 : Charger les données
    # ========================================================================
    print("📥 Chargement des données...")
    ratings_path = data_processed / "ratings_clean.parquet"
    movies_path = data_processed / "movies_clean.parquet"
    
    if not ratings_path.exists() or not movies_path.exists():
        print("❌ Les fichiers Parquet n'existent pas!")
        print(f"   Exécutez d'abord: python src/preprocess.py")
        spark.stop()
        return
    
    ratings_df = spark.read.parquet(str(ratings_path))
    movies_df = spark.read.parquet(str(movies_path))
    
    print(f"✓ {ratings_df.count():,} évaluations chargées")
    print(f"✓ {movies_df.count():,} films chargés")
    
    # ========================================================================
    # ÉTAPE 2 : Entraîner le modèle ALS
    # ========================================================================
    print("\n🎓 Entraînement du modèle ALS...")
    print("  (Cela peut prendre quelques minutes...)")
    
    als = ALS(
        maxIter=10,
        regParam=0.01,
        userCol="userId",
        itemCol="movieId",
        ratingCol="rating",
        coldStartStrategy="drop",
        nonnegative=True,
        seed=42
    )
    
    als_model = als.fit(ratings_df)
    print("✅ Modèle ALS entraîné !")
    
    # ========================================================================
    # ÉTAPE 3 : Générer les recommandations pour TOUS les utilisateurs
    # ========================================================================
    print("\n📊 Génération des recommandations...")
    
    user_ids = ratings_df.select("userId").distinct()
    
    # Top 50 recommandations par utilisateur
    recommendations_df = als_model.recommendForUserSubset(user_ids, 50)
    
    # Exploser les recommandations
    recommendations_exploded = recommendations_df.select(
        col("userId"),
        explode(col("recommendations")).alias("rec")
    ).select(
        col("userId"),
        col("rec.movieId"),
        col("rec.rating").alias("predicted_rating")
    )
    
    # Joindre avec les films pour avoir les titres
    recommendations_with_titles = recommendations_exploded.join(
        movies_df.select("movieId", "title"),
        on="movieId",
        how="left"
    ).select("userId", "movieId", "title", "predicted_rating")
    
    # ========================================================================
    # ÉTAPE 4 : Sauvegarder les recommandations
    # ========================================================================
    print(f"✓ {recommendations_with_titles.count():,} recommandations générées")
    
    # Sauvegarder en Parquet
    print("\n💾 Sauvegarde des recommandations...")
    reco_parquet = models_dir / "recommendations.parquet"
    recommendations_with_titles.write.mode("overwrite").parquet(str(reco_parquet))
    print(f"✅ Recommandations sauvegardées: {reco_parquet}")
    
    # Sauvegarder aussi en CSV pour l'API (plus rapide pour Pandas)
    reco_csv_dir = models_dir / "recommendations_csv_tmp"
    recommendations_with_titles.coalesce(1).write \
        .option("header", "true") \
        .mode("overwrite") \
        .csv(str(reco_csv_dir))
    
    # Trouver le fichier CSV créé et le renommer
    import os
    csv_files = [f for f in os.listdir(str(reco_csv_dir)) if f.endswith('.csv')]
    if csv_files:
        src_file = reco_csv_dir / csv_files[0]
        dst_file = models_dir / "recommendations.csv"
        import shutil
        shutil.move(str(src_file), str(dst_file))
        shutil.rmtree(str(reco_csv_dir))
        print(f"✅ Recommandations CSV sauvegardées: {dst_file}")
    else:
        print("⚠️  Pas de fichier CSV trouvé")
    
    # ========================================================================
    # RÉSUMÉ
    # ========================================================================
    elapsed_time = time.time() - start_time
    print("\n" + "=" * 70)
    print(f"✨ Entraînement terminé en {elapsed_time:.1f} secondes !")
    print(f"   Modèle ALS sauvegardé dans: {models_dir}")
    print("=" * 70)
    
    spark.stop()


if __name__ == "__main__":
    train_als()
