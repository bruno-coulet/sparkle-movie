# Sparkle Movie - Systeme de recommandation MovieLens

## Projet
- Objectif: construire un systeme de recommandation de films (ALS, contenu, KNN) avec Spark.
- Entrees actuelles: donnees nettoyees en Parquet dans data/processed.
- API actuelle: FastAPI expose des endpoints de statistiques et de recommandations baseline.
- Cible: brancher l'API sur le modele ALS entraine ou sur un dataset Top-10 genere offline.

## Objectif
Comparer plusieurs approches de recommandation personnalisee a partir de MovieLens:
- filtrage collaboratif ALS (Spark MLlib)
- recommandation basee contenu
- recommandation user-user (KNN)

Le projet est organise en deux notebooks:
1. EDA et preparation des donnees: [notebooks/eda.ipynb](notebooks/eda.ipynb)
2. Modelisation et evaluation: [notebooks/model.ipynb](notebooks/model.ipynb)

## Stack
- Python 3.12
- Gestion d'environnement: uv
- PySpark 3.5.x
- Pandas / Matplotlib / Seaborn
- FastAPI

## Architecture

```text
sparkle-movie/
├── README.md
├── pyproject.toml
├── Makefile
├── requirements.txt
├── data/
│   ├── raw/
│   │   ├── movies.csv
│   │   ├── ratings.csv
│   │   ├── tags.csv
│   │   └── links.csv
│   └── processed/
│       ├── ratings_clean.parquet/
│       └── movies_clean.parquet/
├── models/
│   ├── recommendations.csv
│   └── recommendations.parquet/
├── src/
│   ├── __init__.py
│   ├── preprocess.py  # CSV → Parquet
│   └── train.py       # ALS training
├── api/
│   ├── main.py        # FastAPI app
│   ├── config.py      # Configuration
│   ├── startup.py     # Spark resources
│   ├── schemas.py     # Pydantic models
│   ├── routes/
│   │   └── recommendations.py
│   └── services/
│       └── recommendation_service.py
├── streamlit/
│   ├── __init__.py
│   ├── app.py         # Streamlit frontend
│   ├── config.py      # Frontend config
│   └── utils.py       # Utility functions
├── notebooks/
│   ├── eda.ipynb
│   └── model.ipynb
└── tests/
```

Responsabilites:
- src: fonctions reutilisables Spark et utilitaires de chargement/nettoyage.
- notebooks: experimentation, entrainement et evaluation.
- data/raw_*: donnees brutes MovieLens.
- data/processed: donnees nettoyees consommees par modelisation et API.
- api: exposition HTTP des resultats via FastAPI.

## Demarrage Rapide

### 1) Prerequis systeme (WSL/Linux/macOS)
Spark necessite Java:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install openjdk-17-jdk unzip -y
java -version
```

### 2) Installation de uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source "$HOME/.cargo/env"
```

### 3) Installation des dependances projet

```bash
uv sync
```

### 4) Activation de l'environnement

```bash
source .venv/bin/activate
```

### 5) Lancer Jupyter

```bash
uv run jupyter lab
```

## Donnees
Dataset MovieLens: https://grouplens.org/datasets/movielens/

Tables principales:
- ratings.csv: userId, movieId, rating, timestamp
- movies.csv: movieId, title, genres
- links.csv: movieId, imdbId, tmdbId

## Pipeline Data Science

### Notebook EDA
[notebooks/eda.ipynb](notebooks/eda.ipynb) couvre:
1. chargement Spark
2. controle schema/qualite
3. nettoyage (NA, doublons, bornes)
4. analyses exploratoires
5. export des donnees nettoyees

Artefacts produits (utilises ensuite):
- [data/processed/ratings_clean.parquet](data/processed/ratings_clean.parquet)
- [data/processed/movies_clean.parquet](data/processed/movies_clean.parquet)

### Notebook Model
[notebooks/model.ipynb](notebooks/model.ipynb) couvre:
1. tuning ALS (rank, regParam, maxIter)
2. entrainement final
3. evaluation RMSE et metriques top-K
4. export du modele ALS entraine (cellule de fin)

Export modele ALS:
- Le modele final est sauvegarde dans: artifacts/als_model
- Cette sauvegarde sert de base de reutilisation pour l'API ou un job batch.

## API FastAPI

Le module [api/app.py](api/app.py) lit actuellement les donnees nettoyees depuis data/processed et expose:
- /nombre_utilisateurs
- /nombre_films_notes
- /statistiques
- /recommandations/{user_id}
- /genres
- /docs

Lancer l'API:

```bash
uv run uvicorn api.app:app --host 127.0.0.1 --port 8000
```

## Strategie ALS Pour Gros Volume

Pour un dataset tres grand, le pattern recommande est:
1. entrainement ALS offline (Spark batch)
2. generation offline d'un Top-10 par utilisateur
3. lecture rapide de ce Top-10 par l'API

Pourquoi:
- eviter de recalculer ALS en temps reel dans une requete HTTP
- stabiliser la latence API
- mieux scaler horizontalement

Schema cible du dataset de recommandations:
- userId
- movieId
- score
- rank
- run_date

## Feuille de Route
1. ajouter un job batch qui genere recommandations_top10.parquet a partir du modele ALS.
2. ajouter un endpoint API qui lit ces recommandations par userId.
3. implementer un fallback cold-start (top populaires) si user inconnu.

## Notes Implementation
- Utiliser get_project_root() dans [src/utils.py](src/utils.py) pour des chemins robustes.
- Garder le nettoyage dans EDA et la modelisation sur data/processed pour la reproductibilite.

## Lancer le projet avec Docker

### 1) Prérequis
- Docker
- Docker Compose

### 2) Créer un fichier docker-compose.yml
```
version: "3.8"
services:
  sparkle-movie:
    build: .
    ports:
      - "8000:8000"
    environment:
      - SPARK_HOME=/usr/local/spark
      - JAVA_HOME=/usr/lib/jvm/java-17-openjdk
    volumes:
      - ./data:/data
      - ./models:/models
      - ./src:/src
```

### 3) Lancer le projet
```bash
docker-compose up
```
