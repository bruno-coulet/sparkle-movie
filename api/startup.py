"""Gestion des ressources Spark pour l'API."""

from pyspark.sql import SparkSession
from pathlib import Path
import pandas as pd


class SparkResourceManager:
    """Singleton pour gérer les ressources Spark de l'application."""
    
    _spark_session = None
    _data_cache = {}
    
    @classmethod
    def get_spark_session(cls) -> SparkSession:
        """Retourne la session Spark (lazy initialization)."""
        if cls._spark_session is None:
            cls._spark_session = SparkSession.builder \
                .appName("sparkle-movie-api") \
                .master("local[*]") \
                .config("spark.driver.memory", "4g") \
                .config("spark.sql.shuffle.partitions", "200") \
                .getOrCreate()
            
            cls._spark_session.sparkContext.setLogLevel("WARN")
        
        return cls._spark_session
    
    @classmethod
    def get_data(cls):
        """Charge les données Spark (ratings + movies) et les met en cache."""
        if "ratings" in cls._data_cache:
            return cls._data_cache["ratings"], cls._data_cache["movies"]
        
        spark = cls.get_spark_session()
        project_root = Path(__file__).parent.parent
        data_dir = project_root / "data" / "processed"
        
        ratings = spark.read.parquet(str(data_dir / "ratings_clean.parquet"))
        movies = spark.read.parquet(str(data_dir / "movies_clean.parquet"))
        
        ratings.cache()
        movies.cache()
        
        cls._data_cache["ratings"] = ratings
        cls._data_cache["movies"] = movies
        
        return ratings, movies
    
    @classmethod
    def get_recommendations_df(cls) -> pd.DataFrame:
        """Charge les recommandations ALS pré-calculées."""
        if "recommendations" in cls._data_cache:
            return cls._data_cache["recommendations"]
        
        project_root = Path(__file__).parent.parent
        models_dir = project_root / "models"
        recs_path = models_dir / "recommendations.csv"
        
        if not recs_path.exists():
            raise FileNotFoundError(f"Recommendations file not found: {recs_path}")
        
        df = pd.read_csv(recs_path)
        cls._data_cache["recommendations"] = df
        return df
    
    @classmethod
    def stop(cls):
        """Arrête la session Spark et libère les ressources."""
        if cls._spark_session is not None:
            cls._spark_session.stop()
            cls._spark_session = None
        cls._data_cache.clear()
