# Sparkle Movie - Systeme de recommandation MovieLens

## Projet
Système de recommandation de films basé sur MovieLens avec:
- **Backend**: API FastAPI exposant les recommandations ALS Spark
- **Frontend**: Interface Streamlit style Netflix pour l'exploration interactive
- **ML**: Filtrage collaboratif ALS avec Spark MLlib sur grand dataset (330k users, 33M ratings)
- **Data**: Données nettoyées en Parquet (movies_clean.parquet, ratings_clean.parquet)

## Stack
- **Python**: 3.12
- **Environnement**: uv
- **ML/Big Data**: PySpark 3.5.x (MLlib)
- **Backend API**: FastAPI + Uvicorn
- **Frontend Web**: Streamlit 1.28+
- **Data**: Apache Parquet format
- **Orchestration**: Docker + Docker Compose (optionnel)

## Jeu de donné MovieLens

Le traitement du grand jeu de donnée de 335 MB est fait sur **colab** en clonant le repo github sur **googledrive**
La version nettoyé des données et les models entrainés sont à télécharger depuis https://drive.google.com/drive/folders/1A80Gl-IPq1H--me0zlXq5Hrtz0nlvvWH?usp=sharing

## Architecture

```
sparkle-movie/
├── README.md
├── pyproject.toml
├── docker-compose.yml
├── Dockerfile                 # Image API (avec Java pour Spark)
├── Dockerfile.frontend        # Image Streamlit (légère)
├── api/
│   ├── main.py               # Point d'entrée FastAPI
│   ├── config.py             # Configuration
│   ├── startup.py            # SparkResourceManager (Singleton)
│   ├── schemas.py            # Modèles Pydantic
│   ├── routes/
│   │   └── recommendations.py  # Endpoints /api/*
│   └── services/
│       └── recommendation_service.py  # Logique métier
├── frontend/
│   ├── app.py                # Application Streamlit
│   ├── config.py             # Configuration (API_URL)
│   └── utils.py              # Helpers (fetch_*)
├── data/
│   ├── raw_big/              # Données brutes MovieLens 235 MB
│   ├── raw_small/            # Subset pour EDA
│   └── processed/
│       ├── ratings_clean.parquet/    # ⚠️ Non versionné (télécharger depuis Google Drive)
│       └── movies_clean.parquet/     # ⚠️ Non versionné (télécharger depuis Google Drive)
├── models/
│   ├── als_model/            # Modèle ALS Spark sauvegardé
│   └── recommendations.csv   # Recommandations pré-calculées
├── src/
│   ├── preprocess.py         # CSV → Parquet
│   └── train.py              # Entraînement ALS
├── notebooks/
│   ├── eda.ipynb
│   └── model.ipynb
└── tests/
```

**Points clés:**
- `api/main.py`: Point d'entrée FastAPI unique (routes avec préfixe `/api`)
- `startup.py`: Gestion du cycle de vie Spark (lazy init, singleton)
- `frontend/app.py`: Une page unique, design Netflix, appelle `/api/*`
- Données Parquet (ratings_clean, movies_clean) doivent être présentes localement

## Démarrage Rapide

### 1) Prérequis systèmе

Spark nécessite Java 17+:
```bash
# macOS
brew install openjdk@17
java -version  # Doit afficher "openjdk version 17"

# Linux (Ubuntu/Debian)
sudo apt install openjdk-17-jdk-headless -y
java -version
```

### 2) Installation de uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source "$HOME/.cargo/env"
```

### 3) Clone et setup du projet

```bash
git clone https://github.com/brunocoulet/sparkle-movie.git
cd sparkle-movie
git checkout app  # Branche avec API + Streamlit complets
uv sync           # Installe toutes les dépendances
```

### 4) ⚠️ Données requises

Les fichiers Parquet doivent être présents localement:
```bash
# Télécharger depuis Google Drive et placer dans :
data/processed/
├── ratings_clean.parquet/
└── movies_clean.parquet/
```

Pour le déploiement de production, l'API lit directement `data/processed/`.
Le sous-dossier `small/` peut rester utile pour les notebooks, mais il n'est
pas nécessaire au démarrage de l'API si les deux Parquet racine sont présents.

**Sans ces fichiers, l'API ne peut pas démarrer.**

### 5) Lancer le système complet

**Option A: En local (2 terminaux)**

Terminal 1 - API FastAPI:
```bash
uv run uvicorn api.main:app --host 127.0.0.1 --port 8001
```

Terminal 2 - Frontend Streamlit:
```bash
uv run streamlit run frontend/app.py --server.port 8501
```

Puis ouvrir: http://127.0.0.1:8501

**Option B: Avec Docker**

```bash
docker-compose up --build
# API: http://localhost:8000
# Streamlit: http://localhost:8501
```

## Endpoints API

### `/api/statistiques`
Statistiques globales du dataset.
```bash
curl http://127.0.0.1:8001/api/statistiques
# {"total_users": 330975, "total_movies": 86537, "total_ratings": 33832162}
```

### `/api/recommandations/{user_id}`
Recommandations ALS pour un utilisateur.
```bash
curl "http://127.0.0.1:8001/api/recommandations/1?limit=5"
```

### `/api/utilisateur/{user_id}/avis`
Historique des avis d'un utilisateur.
```bash
curl "http://127.0.0.1:8001/api/utilisateur/1/avis?limit=10"
```

### `/api/genres`
Genres populaires.
```bash
curl http://127.0.0.1:8001/api/genres
```

### `/docs`
Documentation Swagger interactive.
```
http://127.0.0.1:8001/docs
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

## Architecture Backend

### API FastAPI (`api/main.py`)

L'API expose des endpoints avec préfixe `/api`:

```python
app = FastAPI(title="Sparkle Movie API", version="1.0.0")
app.include_router(recommendations_router)  # Préfixe: /api
```

**Middleware CORS:** Tous les domaines autorisés (configuré pour Streamlit).

**Lifespan:** Initialise Spark et les données au démarrage.

### SparkResourceManager (`api/startup.py`)

Singleton qui gère:
- **Session Spark**: Lazy init avec `master("local[*")`, 4GB de RAM
- **Cache**: Mémorisation en mémoire des DataFrames ratings/movies
- **Recommandations**: Chargemement du CSV pré-calculé ou du modèle ALS

Exemple d'utilisation:
```python
spark = SparkResourceManager.get_spark_session()
ratings_df, movies_df = SparkResourceManager.get_data()
recs_df = SparkResourceManager.get_recommendations_df()
```

### Frontend Streamlit (`frontend/app.py`)

Page unique style Netflix avec:
- **Sidebar**: Sélection utilisateur, paramètres, stats globales
- **Section 1**: Profil utilisateur (films notés, moyenne, meilleure/pire note)
- **Section 2**: Historique des avis (tableau scrollable)
- **Section 3**: Recommandations en grille visuelle

**Configuration** (`frontend/config.py`):
```python
API_URL = "http://127.0.0.1:8001"  # À adapter en prod
REQUEST_TIMEOUT = 30
```

**Utilitaires** (`frontend/utils.py`):
```python
@st.cache_data(ttl=300)
def fetch_statistics() -> Optional[dict]:
    """Récupère /api/statistiques avec cache 5min."""

def fetch_recommendations(user_id: int, limit: int = 10) -> Optional[dict]:
    """Récupère /api/recommandations/{user_id}."""
```

## Statut des branches

| Branch | Contenu | État |
|--------|---------|------|
| `main` | Notebooks d'expérimentation, API basique | ✅ Fonctionnel |
| `large` | Traitement du grand dataset sur Colab | ⏳ Non exécuté localement |
| `app` | API + Streamlit complets | ✅ Production-ready |

**Recommandation:** Travailler sur la branche `app` pour avoir l'interface + API complètes.

## Données et artefacts

### Dépendances non-versionnées (trop volumineux)

- `data/processed/ratings_clean.parquet/` (~12 GB)
- `data/processed/movies_clean.parquet/` (~100 MB)
- `models/als_model/` (modèle Spark sauvegardé)
- `models/recommendations.csv` (top-10 par utilisateur)
- `data/processed/small/` (optionnel, utile seulement pour les notebooks de test)

**Localisation actuelle:** Google Drive (lien à demander à l'équipe)

### Données versionnées

- `data/raw_small/`: Subset MovieLens 100K (petit dataset de test)
- Notebooks: EDA et entraînement ALS

## Próchaines étapes

1. **Optimisation Spark**: Tuner `spark.sql.shuffle.partitions` et mémoire driver
2. **Cache Redis**: Remplacer le cache in-memory par Redis pour scalabilité
3. **Authentification**: Ajouter API key / JWT si exposition internet
4. **Monitoring**: Logs structurées JSON, endpoint `/metrics`
5. **Tests**: Suite pytest pour endpoints + services
6. **CI/CD**: Pipeline GitHub Actions (lint → test → docker build)
>>>>>>> 4d71bd3 (Update: README + frontend config pour branche app avec grand dataset)

## Notes Implementation
- Utiliser get_project_root() dans [src/utils.py](src/utils.py) pour des chemins robustes.
- Garder le nettoyage dans EDA et la modelisation sur data/processed pour la reproductibilite.
