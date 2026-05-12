# Frontend Streamlit - Sparkle Movie

## Installation

Installez les dépendances ajoutées (Streamlit et requests) :

```bash
# Assurez-vous que l'env virtuel est activé
source .venv/bin/activate

# Installez les dépendances via uv
uv sync
```

## Lancer l'application

### Étape 1 : Démarrer l'API FastAPI

Dans un premier terminal :

```bash
# Activez l'env virtuel
source .venv/bin/activate

# Lancez l'API sur le port 8000
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

L'API sera accessible sur : `http://localhost:8000`
Documentation interactive : `http://localhost:8000/docs`

### Étape 2 : Démarrer Streamlit

Dans un second terminal :

```bash
# Activez l'env virtuel
source .venv/bin/activate

# Lancez l'application Streamlit
streamlit run front/app.py
```

Streamlit ouvrira automatiquement l'application dans votre navigateur sur `http://localhost:8501`

## Fonctionnalités

✅ **Statistiques Globales** - Consultez les informations du dataset  
✅ **Recommandations Personnalisées** - Obtenez les films recommandés par utilisateur  
✅ **Genres Populaires** - Explorez les genres avec visualisations  
✅ **Interface Interactive** - Design moderne avec Streamlit

## Architecture

```
Frontend (Streamlit)  ←→  API (FastAPI)  ←→  Backend (PySpark)
   :8501                    :8000              Spark Session
```

- Le frontend Streamlit appelle l'API FastAPI via HTTP
- L'API récupère les données depuis les fichiers Parquet avec Spark
- Les données sont cachées en mémoire pour les performances

## Configuration CORS

L'API a été configurée pour accepter les requêtes CORS depuis n'importe quelle source.
En production, limitez les origines autorisées dans [api/main.py](../api/main.py).

## Dépannage

**L'application dit que l'API n'est pas accessible ?**
- Vérifiez que l'API FastAPI est en cours d'exécution sur `http://localhost:8000`
- Testez avec : `curl http://localhost:8000/statistiques`

**Les données Parquet ne se chargent pas ?**
- Vérifiez que les fichiers existent dans `data/processed/`:
  - `ratings_clean.parquet`
  - `movies_clean.parquet`
