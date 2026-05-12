"""
Application Streamlit style Netflix pour l'API MovieLens Spark.
Une page unique, design épuré et fluide.
"""

import sys, os
from pathlib import Path

# Ajouter le dossier frontend au sys.path pour les imports
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
import streamlit as st
from config import PAGE_CONFIG
from utils import (
    fetch_genres,
    fetch_recommendations,
    fetch_statistics,
    fetch_user_ratings,
)

# Configuration de la page Streamlit
st.set_page_config(**PAGE_CONFIG)

# Custom CSS pour style Netflix
st.markdown(
    """
<style>
    /* Général */
    body {
        background-color: #0F0F0F;
    }
    
    /* Titre principal */
    .hero-title {
        font-size: 3rem;
        font-weight: bold;
        color: white;
        margin-bottom: 10px;
    }
    
    .hero-subtitle {
        font-size: 1.1rem;
        color: #B3B3B3;
        margin-bottom: 20px;
    }
    
    /* Section titles */
    .section-title {
        font-size: 1.5rem;
        font-weight: bold;
        color: white;
        margin-top: 40px;
        margin-bottom: 20px;
        border-left: 4px solid #FF6B6B;
        padding-left: 12px;
    }
    
    /* Cards */
    .movie-card {
        background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
        border: 1px solid #333;
        border-radius: 8px;
        padding: 20px;
        text-align: center;
        transition: transform 0.3s, box-shadow 0.3s;
    }
    
    .movie-card:hover {
        transform: scale(1.05);
        box-shadow: 0 8px 24px rgba(255, 107, 107, 0.3);
    }
    
    /* Métriques */
    .metric-box {
        background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
        border: 1px solid #333;
        border-radius: 8px;
        padding: 20px;
        text-align: center;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ============================================================================
# SIDEBAR - CONTRÔLES
# ============================================================================

with st.sidebar:
    st.title("Sparkle Movie")
    st.divider()

    st.subheader("Paramètres")

    user_id = st.number_input(
        label="Sélectionner un utilisateur", min_value=1, max_value=610, value=1, step=1
    )

    limit_reco = st.slider("Nombre de recommandations", min_value=4, max_value=20, value=8, step=1)

    st.divider()

    # Stats globales en sidebar
    st.subheader("Dataset")
    stats = fetch_statistics()
    if stats:
        st.metric("Utilisateurs", f"{stats['total_users']:,}")
        st.metric("Films", f"{stats['total_movies']:,}")
        st.metric("Avis", f"{stats['total_ratings']:,}")

# ============================================================================
# MAIN CONTENT - UNE PAGE NETFLIX STYLE
# ============================================================================

# Hero Section
st.markdown(
    """
<div style="background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%); 
            border-radius: 12px; padding: 40px; margin-bottom: 40px; border: 1px solid #333;">
    <h1 style="color: #FF6B6B; font-size: 2.5rem; margin: 0;">Sparkle Movie</h1>
    <p style="color: #B3B3B3; font-size: 1.1rem; margin: 10px 0 0 0;">
        Recommandations cinéma basées sur le machine learning
    </p>
</div>
""",
    unsafe_allow_html=True,
)

# ============================================================================
# SECTION 1 : STATISTIQUES UTILISATEUR
# ============================================================================

st.markdown(
    '<div class="section-title">Votre Profil (Utilisateur #' + str(user_id) + ")</div>",
    unsafe_allow_html=True,
)

with st.spinner("Chargement du profil..."):
    user_ratings = fetch_user_ratings(user_id, limit=100)

if user_ratings and user_ratings.get("avis"):
    avis_list = user_ratings["avis"]
    notes = [a["rating"] for a in avis_list]

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f"""
        <div class="metric-box">
            <p style="color: #B3B3B3; margin: 0;">Films notés</p>
            <p style="color: #FF6B6B; font-size: 2rem; font-weight: bold; margin: 10px 0 0 0;">{len(avis_list)}</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        avg_note = sum(notes) / len(notes)
        st.markdown(
            f"""
        <div class="metric-box">
            <p style="color: #B3B3B3; margin: 0;">Moyenne</p>
            <p style="color: #FF6B6B; font-size: 2rem; font-weight: bold; margin: 10px 0 0 0;">{avg_note:.1f}/5</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f"""
        <div class="metric-box">
            <p style="color: #B3B3B3; margin: 0;">Meilleure note</p>
            <p style="color: #FF6B6B; font-size: 2rem; font-weight: bold; margin: 10px 0 0 0;">{max(notes):.1f}/5</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
            f"""
        <div class="metric-box">
            <p style="color: #B3B3B3; margin: 0;">Pire note</p>
            <p style="color: #FF6B6B; font-size: 2rem; font-weight: bold; margin: 10px 0 0 0;">{min(notes):.1f}/5</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

# ============================================================================
# SECTION 2 : AVIS UTILISATEUR
# ============================================================================

st.markdown('<div class="section-title">Vos Avis Récents</div>', unsafe_allow_html=True)

if user_ratings and user_ratings.get("avis"):
    avis_list = user_ratings["avis"][:15]  # Top 15 avis récents

    avis_df = pd.DataFrame(
        [
            {
                "Film": a["title"][:40],
                "Note": "★" * int(a["rating"]) + "☆" * (5 - int(a["rating"])),
                "Évaluation": f"{a['rating']:.1f}/5",
            }
            for a in avis_list
        ]
    )

    st.dataframe(avis_df, use_container_width=True, hide_index=True)
else:
    st.info("Aucun avis trouvé pour cet utilisateur.")

# ============================================================================
# SECTION 3 : RECOMMANDATIONS EN CARTES
# ============================================================================

st.markdown('<div class="section-title">Pour vous</div>', unsafe_allow_html=True)

with st.spinner("Calcul des recommandations..."):
    recommendations = fetch_recommendations(user_id, limit=limit_reco)

if recommendations and recommendations.get("recommendations"):
    reco_list = recommendations["recommendations"]

    st.markdown(f"**{len(reco_list)} films recommandés** - Modèle ALS")

    # Grille de cartes
    cols_per_row = 4
    for i in range(0, len(reco_list), cols_per_row):
        cols = st.columns(cols_per_row)

        for col_idx, col in enumerate(cols):
            if i + col_idx < len(reco_list):
                movie = reco_list[i + col_idx]
                score = movie.get("predicted_rating", 0)
                rank = i + col_idx + 1

                with col:
                    st.markdown(
                        f"""
                    <div class="movie-card">
                        <p style="font-size: 2rem; color: #FF6B6B; margin: 0; font-weight: bold;">#{rank}</p>
                        <p style="color: white; font-size: 1rem; margin: 15px 0 10px 0; font-weight: bold; line-height: 1.3;">
                            {movie["title"][:30]}
                        </p>
                        <p style="color: #B3B3B3; font-size: 0.9rem; margin: 0;">Score ALS</p>
                        <p style="color: #FF6B6B; font-size: 1.5rem; margin: 8px 0 0 0; font-weight: bold;">
                            {score:.2f}/10
                        </p>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

# ============================================================================
# SECTION 4 : GENRES POPULAIRES
# ============================================================================

st.markdown('<div class="section-title">Genres Populaires</div>', unsafe_allow_html=True)

with st.spinner("Chargement des genres..."):
    genres_data = fetch_genres()

if genres_data and genres_data.get("genres"):
    top_genres = genres_data["genres"][:12]

    genres_df = pd.DataFrame(
        [{"Genre": g["genre"], "Évaluations": g["n_ratings"]} for g in top_genres]
    )

    col1, col2 = st.columns([1, 1.5])

    with col1:
        st.dataframe(genres_df, use_container_width=True, hide_index=True)

    with col2:
        chart_data = genres_df.set_index("Genre")
        st.bar_chart(chart_data["Évaluations"], height=350)

# ============================================================================
# FOOTER
# ============================================================================

st.divider()
st.markdown(
    """
<div style="text-align: center; color: #B3B3B3; padding: 20px;">
    <p>Modèle ALS (Alternating Least Squares) | MovieLens Small Dataset | Sparkle Movie</p>
</div>
""",
    unsafe_allow_html=True,
)
