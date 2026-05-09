"""Configuration de l'API FastAPI."""

from pathlib import Path

# Chemins
PROJECT_ROOT = Path(__file__).parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
MODELS_DIR = PROJECT_ROOT / "models"

# Configuration Spark
SPARK_MASTER = "local[*]"
SPARK_DRIVER_MEMORY = "4g"
SPARK_LOG_LEVEL = "WARN"

# Configuration API
API_HOST = "0.0.0.0"
API_PORT = 8000
API_RELOAD = True

# CORS
CORS_ORIGINS = ["*"]
CORS_CREDENTIALS = True
CORS_METHODS = ["*"]
CORS_HEADERS = ["*"]

# Timeouts
REQUEST_TIMEOUT = 30
