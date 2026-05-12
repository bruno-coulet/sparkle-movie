"""
Utilitaires pour le frontend Streamlit.
"""

from typing import Optional

import requests
import streamlit as st

# from frontend.config import API_URL, REQUEST_TIMEOUT
from config import API_URL, REQUEST_TIMEOUT


@st.cache_data(ttl=300)
def fetch_statistics() -> Optional[dict]:
    """Récupère les statistiques globales."""
    try:
        response = requests.get(f"{API_URL}/api/statistiques", timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Erreur lors du chargement des statistiques: {e}")
        return None


@st.cache_data(ttl=300)
def fetch_genres() -> Optional[dict]:
    """Récupère les genres populaires."""
    try:
        response = requests.get(f"{API_URL}/api/genres", timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Erreur lors du chargement des genres: {e}")
        return None


def fetch_recommendations(user_id: int, limit: int = 10) -> Optional[dict]:
    """Récupère les recommandations pour un utilisateur."""
    try:
        response = requests.get(
            f"{API_URL}/api/recommandations/{user_id}",
            params={"limit": limit},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Erreur lors du chargement des recommandations: {e}")
        return None


def fetch_user_ratings(user_id: int, limit: int = 50) -> Optional[dict]:
    """Récupère l'historique des avis d'un utilisateur."""
    try:
        response = requests.get(
            f"{API_URL}/api/utilisateur/{user_id}/avis",
            params={"limit": limit},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Erreur lors du chargement des avis: {e}")
        return None
