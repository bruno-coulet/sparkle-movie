# Instructions Générales de Développement — Sparkle Movie

## Identité du projet
- Projet : système de recommandation de films (MovieLens + ALS + FastAPI + Streamlit)
- Étudiant : alternance Data/IA, 3e année, Marseille
- Niveau cible : code professionnel, commentaires pédagogiques

---

## Comportement de l'agent

- Agis comme un mentor senior en Data Science / MLOps
- Explique brièvement tes choix techniques en français après chaque bloc de code
- Si plusieurs approches existent, présente la plus simple d'abord, puis la plus robuste
- Ne jamais modifier un fichier sans avoir d'abord analysé ses imports et ses dépendances

---

## Stack technique

| Couche | Technologie | Version |
|--------|-------------|---------|
| Langage | Python | 3.12 |
| Gestion env | uv | latest |
| Big Data | PySpark (MLlib) | 3.5.x |
| API | FastAPI + Uvicorn | latest |
| Frontend | Streamlit | >= 1.28 |
| Tests | Pytest | >= 8.0 |
| Lint | Ruff | latest |
| Container | Docker + Docker Compose | latest |
| CI/CD | GitHub Actions | - |
| Runtime Java | OpenJDK 17 | requis par Spark |

---

## Environnement de développement

- OS supportés : Windows 11 (PowerShell), macOS 12+ (Bash/Zsh)
- Toujours utiliser un environnement virtuel via `uv` :
  ```bash
  uv sync              # installe toutes les dépendances
  source .venv/bin/activate   # macOS/Linux
  .venv\Scripts\activate      # Windows PowerShell
  ```
- Ne jamais utiliser `pip install` directement — passer par `uv add <package>`
- Vérifier la disponibilité des imports avant toute modification :
  ```bash
  uv run python -c "import pyspark; print(pyspark.__version__)"
  ```

---

## Règles de code

### Style général
- Typage Python obligatoire sur toutes les fonctions (`typing` ou annotations natives 3.12)
- Docstrings claires sur toutes les fonctions (format Google Style)
- Commentaires en français, code en anglais (noms de variables, fonctions, classes)
- Aucun emoji dans les commentaires, docstrings ou logs
- Longueur de ligne : 100 caractères max

### Cartouche obligatoire
Tout fichier fonctionnel et finalisé doit commencer par ce cartouche :

```python
# =============================================================================
# Projet      : Sparkle Movie
# Fichier     : <nom_du_fichier.py>
# Description : <description en une ligne>
# Auteur      : <prénom nom>
# Date        : <YYYY-MM-DD>
# Version     : 1.0.0
# =============================================================================
```

### Logging
- Toujours utiliser le module `logging` Python, jamais `print()` en production
- Format structuré JSON pour les logs API (voir `api/logging_config.py`)
- Niveau INFO pour les opérations normales, WARNING pour les cas limites, ERROR pour les exceptions

### Gestion des erreurs
- Toujours wrapper les appels Spark dans des try/except avec log explicite
- Les endpoints FastAPI doivent lever des `HTTPException` avec des messages clairs
- Ne jamais laisser passer une exception silencieuse

---

## Architecture du projet

```
sparkle-movie/
├── .github/
│   └── workflows/
│       └── ci.yml          # lint → tests → docker build
├── api/
│   ├── middleware/
│   │   └── logging_middleware.py   # log chaque requête HTTP
│   ├── routes/
│   │   └── recommendations.py      # endpoints HTTP
│   ├── services/
│   │   └── recommendation_service.py  # logique métier
│   ├── config.py
│   ├── logging_config.py
│   ├── main.py             # lifespan + middleware + routes
│   ├── schemas.py          # modèles Pydantic
│   └── startup.py          # SparkResourceManager Singleton
├── data/
│   ├── raw/                # CSV MovieLens bruts (non versionnés)
│   └── processed/          # Parquet nettoyés (non versionnés)
├── frontend/
│   ├── app.py              # interface Streamlit
│   ├── config.py           # API_URL depuis variable d'env
│   └── utils.py            # fonctions fetch_* avec cache
├── models/
│   ├── recommendations.csv # top-50 recs par user (lu par l'API)
│   ├── recommendations.parquet/
│   └── rmse.txt            # RMSE du dernier entraînement (lu par CI)
├── notebooks/
│   ├── eda.ipynb
│   └── model.ipynb
├── src/
│   ├── preprocess.py       # CSV → Parquet
│   └── train.py            # ALS → recommendations.csv + rmse.txt
├── tests/
│   └── test_api.py         # pytest avec mocks Spark
├── .dockerignore
├── .streamlit/
│   └── config.toml
├── docker-compose.yml      # orchestre API + frontend
├── Dockerfile              # image API (multi-stage, Java inclus)
├── Dockerfile.frontend     # image Streamlit (légère, sans Java)
├── Makefile
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

## Docker — règles et explications

### Pourquoi deux Dockerfiles ?
- `Dockerfile` : image API lourde (~1.5 Go) car PySpark nécessite Java 17
- `Dockerfile.frontend` : image légère (~200 Mo) Streamlit only, sans Java
- Séparer permet de ne pas embarquer Java inutilement dans le frontend

### Pattern multi-stage (Dockerfile API)
```dockerfile
# Stage 1 : builder — installe les dépendances avec uv
FROM python:3.12-slim AS builder
# Stage 2 : runtime — copie uniquement le .venv final
FROM python:3.12-slim AS runtime
COPY --from=builder /app/.venv /app/.venv
```
Avantage : l'image finale ne contient pas les outils de build → plus légère et plus sécurisée

### Variables d'environnement Docker
- `API_URL` : injecté dans le frontend via `docker-compose.yml`
- En local : `API_URL=http://localhost:8000`
- En Docker : `API_URL=http://api:8000` (nom du service Docker, pas localhost)
- Le code frontend lit : `API_URL = os.getenv("API_URL", "http://localhost:8000")`

### Commandes Docker essentielles
```bash
# Premier lancement (build + démarrage)
docker compose up --build

# Relance rapide (sans rebuild)
docker compose up

# Arrêt propre
docker compose down

# Voir les logs en temps réel
docker compose logs -f api
docker compose logs -f frontend

# Rebuild uniquement l'API
docker compose build api
```

### Données et volumes
Les fichiers `data/` et `models/` sont montés en volume depuis l'hôte :
```yaml
volumes:
  - ./data:/app/data:ro      # lecture seule
  - ./models:/app/models:ro  # lecture seule
  - ./logs:/app/logs         # écriture des logs
```
Ils ne sont PAS copiés dans l'image Docker (voir `.dockerignore`)

---

## MLOps — règles du projet

### Pipeline de données (à exécuter dans l'ordre)
```bash
# Étape 1 : nettoyer et convertir les données
uv run python src/preprocess.py

# Étape 2 : entraîner ALS et générer les recommandations
uv run python src/train.py
# → produit models/recommendations.csv
# → produit models/rmse.txt

# Étape 3 : démarrer l'API + frontend
bash run.sh
# ou en Docker :
docker compose up --build
```

### Seuil RMSE
- Seuil d'alerte défini à **1.2** (testé automatiquement en CI)
- Si RMSE >= 1.2, le build CI échoue et le modèle ne passe pas en prod
- Réentraîner avec des hyperparamètres différents dans `src/train.py`

### Cold-start
- Utilisateur inconnu → fallback sur top films populaires (avg_rating + min 50 votes)
- Toujours retourner HTTP 200 avec `"note": "Utilisateur inconnu..."` dans le JSON
- Ne jamais retourner 404 pour un user inconnu

### Monitoring
- Endpoint `/metrics` : expose l'état du cache Spark et du modèle
- Endpoint `/health` : vérifié par Docker healthcheck toutes les 30s
- Logs structurés dans `logs/api.log` avec rotation à 10 Mo

---

## Tests

```bash
# Lancer tous les tests
uv run pytest tests/ -v

# Lancer un test spécifique
uv run pytest tests/test_api.py::TestRecommendationsEndpoint -v

# Avec couverture
uv run pytest tests/ --cov=api --cov-report=term-missing
```

### Règles de test
- Spark ne doit JAMAIS démarrer pendant les tests → utiliser `unittest.mock.patch`
- Chaque endpoint doit avoir au minimum : test 200, test 422 (mauvaise entrée)
- Le test RMSE lit `models/rmse.txt` et skip si le fichier est absent

---

## CI/CD — GitHub Actions

Pipeline en 3 jobs séquentiels (un échec bloque les suivants) :

1. **lint** : `ruff check` + `ruff format --check` — vérifie le style sur push
2. **tests** : `pytest tests/` avec Spark mocké — vérifie la logique sur push
3. **docker-build** : build des deux images Docker — uniquement sur `main`

Le "Green Build" = les 3 jobs passent au vert. C'est ce que le jury vérifie.

---

## Snippets utiles

### Tester l'API manuellement
```bash
curl http://localhost:8000/health
curl http://localhost:8000/metrics
curl "http://localhost:8000/api/recommandations/1?limit=5"
curl http://localhost:8000/api/statistiques
curl http://localhost:8000/docs   # ouvrir dans le navigateur
```

### Vérifier que Java est disponible (requis par Spark)
```bash
java -version   # doit afficher openjdk 17
```

### Générer requirements.txt depuis pyproject.toml
```bash
uv pip compile pyproject.toml -o requirements.txt
```

### Colab — si le traitement devient lourd
```python
# Monter Google Drive pour accéder aux données
from google.colab import drive
drive.mount('/content/drive')

# Installer PySpark sur Colab
!pip install pyspark==3.5.0
```