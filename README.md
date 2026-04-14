# Sparkle Movie - Systeme de recommandation MovieLens

## Objectif
Construire et comparer plusieurs approches de recommandation personnalisee a partir de MovieLens:
- filtrage collaboratif avec ALS (Spark MLlib)
- recommandation basee contenu
- recommandation user-user (KNN)

Le projet est organise en deux temps:
1. EDA et preparation des donnees dans [notebooks/eda.ipynb](notebooks/eda.ipynb)
2. Modelisation et evaluation dans un notebook dedie

## Stack
- Python 3.12
- Gestion d'environnement: uv
- PySpark
- Pandas / Matplotlib / Seaborn

## Demarrage

### 1) Pre-requis systeme (WSL/Linux)
Le dua Spark et Windows crée de s problemes de PATH et de parefeu
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

### 3) Environnement Python
```bash
uv venv
source .venv/bin/activate
uv add pyspark pandas matplotlib seaborn ipykernel
```

### 4) Kernel notebook
```bash
uv run python -m ipykernel install --user --name sparkle-movie --display-name sparkle-movie
```

### 5) Lancement
```bash
jupyter lab
```

## Donnees
Dataset MovieLens: https://grouplens.org/datasets/movielens/

Tables principales:
- ratings.csv: userId, movieId, rating, timestamp
- movies.csv: movieId, title, genres
- links.csv: movieId, imdbId, tmdbId

## Workflow [EDA](notebooks/eda.ipynb)
Le notebook [notebooks/eda.ipynb](notebooks/eda.ipynb) couvre:
1. Selection de la source via DATA_SOURCE
2. Chargement Spark + verifications de schema
3. Nettoyage (NA, doublons, bornes de notes)
4. Baseline orientee recommandation
5. Split temporel anti-fuite (train/validation/test)
6. Tendances globales (top films, genres)
7. Sauvegarde des artefacts pour le notebook de modelisation

## Baseline orientee recommandation
Mesures calculees dans l'EDA:
- nombre d'utilisateurs, de films et d'interactions
- densite user-item
- distributions du nombre de notes par utilisateur et par film
- taux d'utilisateurs/items rares (ex: moins de 5 interactions)

Ces indicateurs servent a qualifier:
- la sparsity de la matrice user-item
- la longue traine des items
- la difficulte potentielle pour ALS/KNN

## Split temporel anti-fuite
Le split est base sur timestamp:
- train: interactions les plus anciennes
- validation: interactions intermediaires
- test: interactions les plus recentes

Pourquoi temporel:
- en production, on predit le futur avec le passe
- on evite la fuite d'information d'un split aleatoire (melange passe/futur)

Note reproductibilite:
- le split temporel actuel est deterministe
- une seed (ex: 42) reste utile pour les etapes aleatoires du notebook 2

## Artefacts sauvegardes
Le notebook EDA peut enregistrer automatiquement:
- [data/processed/small/ratings_clean.parquet](data/processed/small/ratings_clean.parquet)
- [data/processed/small/movies_clean.parquet](data/processed/small/movies_clean.parquet)
- [data/processed/small/splits_temporal/train](data/processed/small/splits_temporal/train)
- [data/processed/small/splits_temporal/validation](data/processed/small/splits_temporal/validation)
- [data/processed/small/splits_temporal/test](data/processed/small/splits_temporal/test)

Ces fichiers servent de base stable pour comparer toutes les approches de recommandation.

## Notebook 2 - Plan de modelisation
1. ALS (Spark MLlib)
- tuning de rank, regParam, maxIter
- evaluation RMSE + metriques top-K

2. Recommandation basee contenu
- vecteurs de genres (et/ou TF-IDF)
- similarite cosinus item-item

3. Recommandation user-user (KNN)
- voisins proches sur espace user-item
- aggregation des preferences des voisins

4. Evaluation comparee
- precision@K, recall@K, coverage
- recommandations pour 3 a 5 utilisateurs fictifs

## Remarques implementation
- Utiliser get_project_root() dans [src/utils.py](src/utils.py) pour stabiliser les chemins entre macOS/WSL.
- Preferer le chargement des artefacts processed dans le notebook de modelisation pour eviter de recalculer le nettoyage a chaque run.
