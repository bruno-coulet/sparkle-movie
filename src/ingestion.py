from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, IntegerType, FloatType, LongType
import os

def create_spark_session():
    return SparkSession.builder \
        .appName("MovieLens-Ingestion") \
        .master("local[*]") \
        .getOrCreate()

def main():
    spark = create_spark_session()
    
    # Définition du chemin (relatif à la racine du projet)
    path_ratings = "data/raw/small/ratings.csv"
    
    # 1. Définition du schéma pour ratings.csv
    # userId,movieId,rating,timestamp
    rating_schema = StructType([
        StructField("userId", IntegerType(), True),
        StructField("movieId", IntegerType(), True),
        StructField("rating", FloatType(), True),
        StructField("timestamp", LongType(), True)
    ])

    try:
        print(f"--- Chargement de {path_ratings} ---")
        
        # 2. Lecture du CSV
        df_ratings = spark.read \
            .options(header=True, sep=",") \
            .schema(rating_schema) \
            .csv(path_ratings)

        # 3. Vérifications rapides (Actions Spark)
        print(f"Nombre total de lignes : {df_ratings.count()}")
        
        print("\nAperçu des données :")
        df_ratings.show(5)

        print("\nStatistiques descriptives (colonnes numériques) :")
        df_ratings.select("rating").describe().show()

        # 4. Sauvegarde au format Parquet (plus efficace pour la suite)
        # Parquet garde le schéma en mémoire, contrairement au CSV
        output_path = "data/processed/ratings_clean.parquet"
        print(f"--- Sauvegarde vers {output_path} ---")
        df_ratings.write.mode("overwrite").parquet(output_path)
        
        print("\n✅ Ingestion terminée avec succès !")

    except Exception as e:
        print(f"❌ Erreur lors de l'ingestion : {e}")
    
    finally:
        spark.stop()

if __name__ == "__main__":
    main()