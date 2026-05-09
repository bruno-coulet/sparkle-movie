"""
Application Streamlit pour la visualisation des recommandations.

Configuration de la page unique style Netflix.
"""

# Configuration commune
PAGE_CONFIG = {
    "page_title": "Sparkle Movie",
    "page_icon": "🎬",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
}

# URL de l'API backend
API_URL = "http://127.0.0.1:8001"

# Timeouts
REQUEST_TIMEOUT = 30
