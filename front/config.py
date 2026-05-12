"""
Application Streamlit pour la visualisation des recommandations.

Configuration de la page unique style Netflix.
"""
import os

# Configuration commune
PAGE_CONFIG = {
    "page_title": "Sparkle Movie",
    "page_icon": "🎬",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
}

# URL de l'API backend
# API_URL = "http://127.0.0.1:8001"
# API_URL = os.getenv("API_URL", "http://api:8000")
API_URL = os.getenv("API_URL", "https://api.sparkle-movie.lab.zanza-creation.com/api")

# Timeouts
REQUEST_TIMEOUT = 30
