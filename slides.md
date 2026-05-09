---
marp: true
theme: default
class: invert
paginate: true
style: |
  section {
    background: #141414;
    color: #e5e5e5;
    font-family: 'Helvetica Neue', sans-serif;
  }
  h1 { color: #e50914; font-size: 2.2em; }
  h2 { color: #e50914; border-bottom: 2px solid #e50914; padding-bottom: 8px; }
  h3 { color: #f5a623; }
  strong { color: #e50914; }
  code { background: #2a2a2a; padding: 2px 6px; border-radius: 4px; color: #f5a623; }
  ul li { margin: 10px 0; }
  table { width: 100%; border-collapse: collapse; }
  th { background: #e50914; color: white; padding: 10px; }
  td { padding: 10px; border-bottom: 1px solid #333; }
  .highlight { background: #e50914; padding: 4px 12px; border-radius: 4px; }
---

# 🎬 Sparkle Movie
## Système de recommandation de films

**MovieLens + ALS + FastAPI + Streamlit**

---

## Sommaire

1. Vue d'ensemble du projet
2. Les données — MovieLens
3. Prétraitement des données
4. Algorithme ALS — Comment ça fonctionne ?
5. Évaluation — RMSE & Seuil qualité
6. Architecture — Offline vs Online
7. API — FastAPI & le pattern Singleton
8. Frontend — Streamlit
9. Tests automatisés
10. Docker — Conteneurisation
11. CI/CD — Intégration continue
12. Démo

---

## Vue d'ensemble

```
Données MovieLens
      ↓
  Prétraitement  →  Parquet nettoyé
      ↓
Entraînement ALS  →  recommendations.parquet + rmse.txt
      ↓
   API FastAPI   ←→  Frontend Streamlit
      ↓
   Utilisateur
```

**Principe** : les recommandations sont calculées **une seule fois** en offline.
L'API sert les résultats en temps réel **sans recalcul**.

---

## Les données — MovieLens

- Dataset public de **recommandation de films**
- Contient des **notes** (ratings) données par des utilisateurs à des films
- Format : `userId`, `movieId`, `rating`, `timestamp`

| userId | movieId | rating |
|--------|---------|--------|
| 1      | 296     | 5.0    |
| 1      | 306     | 3.5    |
| 2      | 296     | 4.0    |

**Objectif** : prédire les notes qu'un utilisateur donnerait aux films qu'il n'a pas encore vus.

---

## Prétraitement — `src/preprocess.py`

**Problème** : les données brutes contiennent du bruit (colonnes inutiles, films sans titre...)

**Ce qu'on fait :**
- Suppression des colonnes inutiles (`timestamp`)
- Filtrage des films sans titre
- Conversion des types (`rating` en `float`)
- Sauvegarde en **Parquet** (format colonne, plus rapide que CSV)

**Pourquoi Parquet ?**
→ 5× plus rapide à lire que CSV, compression intégrée, optimal pour Spark

---

## Algorithme ALS — Principe

**ALS = Alternating Least Squares** — Factorisation de matrice

**Le problème** : la matrice utilisateurs × films est **creuse** (98% vide)

```
         Film A  Film B  Film C
User 1     5       ?       3
User 2     ?       4       ?
User 3     2       ?       5
```

**Idée** : décomposer cette grande matrice en deux petites matrices (latentes)
→ **utilisateurs** × facteurs & **films** × facteurs

---

## ALS — Fonctionnement

**Alternating = on alterne** entre deux étapes :

1. On fixe les vecteurs **films** → on optimise les vecteurs **utilisateurs**
2. On fixe les vecteurs **utilisateurs** → on optimise les vecteurs **films**

**10 itérations** → convergence vers la meilleure décomposition

**Résultat** : on peut prédire la note de n'importe quel utilisateur sur n'importe quel film

> "Les utilisateurs qui ont aimé les mêmes films que toi ont aussi aimé X"

---

## Évaluation — RMSE

**RMSE = Root Mean Square Error** — Mesure l'écart entre prédictions et réalité

$$RMSE = \sqrt{\frac{1}{n}\sum(y_{prédit} - y_{réel})^2}$$

**Split 80/20** :
- 80% des notes → entraînement
- 20% des notes → évaluation (jamais vus pendant l'entraînement)

**Notre seuil : RMSE < 1.2**
→ Si RMSE ≥ 1.2, le déploiement est **bloqué automatiquement** par la CI

Résultat sauvegardé dans `models/rmse.txt` → consultable via `/api/metrics`

---

## Architecture — Offline vs Online

### Mode Offline (calcul lourd, une seule fois)
```
src/preprocess.py → src/train.py → recommendations.parquet
```
Durée : plusieurs minutes — fait en avance

### Mode Online (temps réel, rapide)
```
Requête utilisateur → API → lecture cache → réponse < 100ms
```

**Avantage** : l'API ne fait **aucun calcul ML** en temps réel
→ scalable, réponses rapides pour tous les utilisateurs simultanément

---

## API — FastAPI

**FastAPI** : framework Python moderne pour créer des APIs REST

**Nos endpoints :**

| Route | Description |
|-------|-------------|
| `GET /` | Page d'accueil, liste des endpoints |
| `GET /health` | Statut de l'API |
| `GET /api/recommandations/{user_id}` | Top N films recommandés |
| `GET /api/statistiques` | Statistiques du dataset |
| `GET /api/metrics` | RMSE + état du système |

**Validation automatique** avec **Pydantic** : si le paramètre est invalide → 422

---

## API — Le pattern Singleton

**Problème** : Spark est lourd à démarrer (~30s, 4Go RAM)

**Solution** : le **Singleton** — une seule instance partagée par tous

```
Requête 1 → Session Spark créée  ← unique
Requête 2 ─────────────────────┘ (réutilisée)
Requête 3 ─────────────────────┘ (réutilisée)
```

**Lazy initialization** : Spark ne démarre que lors de la première requête

**Lifespan FastAPI** : contrôle le cycle de vie
- Démarrage → initialise Spark, charge les recommandations en mémoire
- Arrêt → ferme proprement la session Spark

---

## API — Schémas Pydantic

**Pydantic** valide les données **dans les deux sens** :

**Entrée** (paramètres de la requête) :
- `user_id` : entier positif obligatoire
- `limit` : entre 1 et 100 (sinon → 422 automatique)

**Sortie** (réponse JSON garantie) :
```json
{
  "user_id": 42,
  "recommendations": [
    { "title": "Inception", "predicted_rating": 4.8 }
  ]
}
```

Si l'utilisateur est inconnu → **HTTP 200** avec liste vide + note explicative (jamais 404)

---

## Frontend — Streamlit

**Streamlit** : framework Python pour créer des interfaces web sans HTML/CSS

**Organisation de l'interface :**
1. Configuration globale + CSS personnalisé
2. Sidebar : saisie `user_id`, bouton recherche
3. Statistiques utilisateur (notes données)
4. Recommandations en **cartes visuelles**
5. Genres populaires
6. Footer

**Communication** : Streamlit appelle l'API via `requests.get()`

---

## Frontend — Cache Streamlit

**Problème** : si chaque rechargement refait tous les appels API → lent

**Solution** : `@st.cache_data(ttl=300)`

```
Statistiques dataset → mises en cache 5 minutes
Genres populaires   → mis en cache 5 minutes
Recommandations     → PAS de cache (personnalisées par user)
```

**Pourquoi cette distinction ?**
- Statistiques/genres : identiques pour tous → cache OK
- Recommandations : uniques par utilisateur → pas de cache

**CORS** : règle de sécurité du navigateur — autorise le frontend (:8501) à appeler l'API (:8000)

---

## Tests automatisés — `tests/test_api.py`

**Problème** : Spark prend 30s à démarrer → tests trop lents

**Solution** : **Mock** — on remplace Spark par un faux objet

```
TestClient ──→ API (vraie)
                 ↓
        SparkResourceManager (mockée)
                 ↓
         MagicMock (instantané)
```

**`scope="module"`** : le TestClient est créé **une seule fois** pour tous les tests
→ 5× plus rapide

**Tests couverts** : health, home, recommandations connues/inconnues, limites invalides, RMSE

---

## Docker — Conteneurisation

**Pourquoi Docker ?** Faire tourner le projet sur n'importe quelle machine identiquement

**Multi-stage build** (Dockerfile API) :
```
Stage 1 — Builder   : installe toutes les dépendances
                          ↓ (copie uniquement le .venv)
Stage 2 — Runtime   : image finale légère, sans les outils de build
```

**Résultat** : image plus petite, plus sécurisée

**Deux images distinctes** :
- `api` (~1.5Go, inclut Java 17 pour Spark)
- `frontend` (~200Mo, Python + Streamlit uniquement)

---

## Docker Compose

**Docker Compose** coordonne les deux services ensemble

**Dépendance intelligente** (`depends_on: condition: service_healthy`) :

```
API démarre → healthcheck /health passe
                    ↓ (seulement alors)
         Frontend démarre
```

→ Le frontend ne démarre **jamais** avant que l'API soit prête

**Volumes** : `data/` et `models/` montés en lecture seule dans l'API
→ Les fichiers Parquet sont accessibles sans être copiés dans l'image

---

## CI/CD — Intégration & Déploiement Continus

**3 jobs séquentiels** (si l'un échoue, les suivants ne tournent pas) :

```
1. lint ──→ 2. tests ──→ 3. docker-build (main uniquement)
```

**Job 1 — lint** : `ruff check` + `ruff format --check`
→ Vérifie la qualité et le style du code

**Job 2 — tests** : `pytest` avec Spark mocké
→ Vérifie que l'API fonctionne (sans démarrer Spark)

**Job 3 — docker-build** : build des deux images
→ Uniquement sur la branche `main` (pas sur les branches de dev)

**Si RMSE ≥ 1.2** → le test `test_rmse_threshold` échoue → déploiement bloqué

---

## Résumé — Choix techniques

| Technologie | Rôle | Pourquoi |
|-------------|------|----------|
| PySpark ALS | Entraînement | Scalable, gère les matrices creuses |
| Parquet | Stockage | 5× plus rapide que CSV |
| FastAPI | API REST | Validation auto, doc Swagger intégrée |
| Singleton | Session Spark | Une seule instance partagée |
| Pydantic | Validation | Données garanties en entrée ET sortie |
| Streamlit | Frontend | Interface Python sans HTML |
| Docker | Déploiement | Reproductible sur toute machine |
| CI/CD | Qualité | Lint + tests avant chaque déploiement |

---

## 🎬 Démo

**Flux complet :**

1. `src/preprocess.py` → nettoie MovieLens
2. `src/train.py` → entraîne ALS, génère `recommendations.parquet`
3. `docker compose up` → démarre API + Frontend
4. `http://localhost:8501` → interface utilisateur
5. Entrer un `user_id` → recommandations personnalisées en < 100ms

**Questions possibles :**
- Pourquoi ALS et pas une autre méthode ?
- Que se passe-t-il si un utilisateur est inconnu ?
- Comment détecter que le modèle vieillit ?
- Pourquoi séparer API et Frontend ?

---

# Merci

**Sparkle Movie** — Système de recommandation de films
MovieLens + ALS + FastAPI + Streamlit + Docker + CI/CD

> *"Les bonnes recommandations, au bon moment, pour le bon utilisateur"*
