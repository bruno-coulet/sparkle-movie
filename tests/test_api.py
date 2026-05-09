# =============================================================================
# Projet      : Sparkle Movie
# Fichier     : tests/test_api.py
# Description : Tests de l'API FastAPI avec mocks Spark (Spark ne demarre pas)
# Auteur      : Sulivan Moreau
# Date        : 2026-04-19
# Version     : 1.0.0
# =============================================================================

from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from api.main import app


def _mock_recs() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "userId": [1, 1, 1, 2, 2],
            "movieId": [10, 20, 30, 40, 50],
            "title": ["Film A", "Film B", "Film C", "Film D", "Film E"],
            "predicted_rating": [4.5, 4.2, 4.0, 3.8, 3.5],
        }
    )


def _mock_spark_df() -> MagicMock:
    """Retourne un DataFrame Spark mocke avec les methodes les plus courantes."""
    df = MagicMock()
    df.filter.return_value = df
    df.join.return_value = df
    df.select.return_value = df
    df.orderBy.return_value = df
    df.limit.return_value = df
    df.distinct.return_value = df
    df.count.return_value = 42
    df.collect.return_value = []
    return df


@pytest.fixture(scope="module")
def client():
    """Client de test avec Spark entierement mocke."""
    mock_df = _mock_spark_df()
    with (
        patch("api.startup.SparkResourceManager.get_data", return_value=(mock_df, mock_df)),
        patch(
            "api.startup.SparkResourceManager.get_recommendations_df",
            return_value=_mock_recs(),
        ),
        patch("api.startup.SparkResourceManager.stop"),
    ):
        with TestClient(app) as c:
            yield c


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------


def test_health_ok(client: TestClient) -> None:
    """L'endpoint /health renvoie status=ok."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "service" in data


# ---------------------------------------------------------------------------
# /
# ---------------------------------------------------------------------------


def test_home_ok(client: TestClient) -> None:
    """L'endpoint racine renvoie le message d'accueil et la liste des endpoints."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "endpoints" in data


# ---------------------------------------------------------------------------
# /api/recommandations/{user_id}
# ---------------------------------------------------------------------------


def test_recommendations_known_user(client: TestClient) -> None:
    """Un utilisateur connu recoit ses recommandations."""
    response = client.get("/api/recommandations/1?limit=2")
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == 1
    assert len(data["recommendations"]) <= 2
    assert all("title" in r and "predicted_rating" in r for r in data["recommendations"])


def test_recommendations_unknown_user(client: TestClient) -> None:
    """Un utilisateur inconnu renvoie HTTP 200 avec liste vide et note explicative."""
    response = client.get("/api/recommandations/99999?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == 99999
    assert data["recommendations"] == []
    assert "note" in data


def test_recommendations_limit_zero(client: TestClient) -> None:
    """limit=0 est invalide — FastAPI doit renvoyer 422."""
    response = client.get("/api/recommandations/1?limit=0")
    assert response.status_code == 422


def test_recommendations_limit_over_max(client: TestClient) -> None:
    """limit > 100 est invalide — FastAPI doit renvoyer 422."""
    response = client.get("/api/recommandations/1?limit=200")
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# /api/statistiques
# ---------------------------------------------------------------------------


def test_statistiques_ok(client: TestClient) -> None:
    """L'endpoint /api/statistiques renvoie les trois compteurs."""
    response = client.get("/api/statistiques")
    assert response.status_code == 200
    data = response.json()
    assert "total_users" in data
    assert "total_movies" in data
    assert "total_ratings" in data


# ---------------------------------------------------------------------------
# RMSE threshold (lit models/rmse.txt, skip si absent)
# ---------------------------------------------------------------------------


def test_rmse_threshold() -> None:
    """Le RMSE enregistre doit etre inferieur au seuil de 1.2."""
    rmse_file = Path(__file__).parent.parent / "models" / "rmse.txt"
    if not rmse_file.exists():
        pytest.skip("models/rmse.txt absent — executez d'abord src/train.py")

    rmse = float(rmse_file.read_text().strip())
    assert rmse < 1.2, f"RMSE trop eleve : {rmse:.4f} >= 1.2"
