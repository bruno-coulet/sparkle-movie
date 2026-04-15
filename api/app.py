"""API FastAPI de démonstration pour servir des recommandations.

Cette version expose un endpoint simple qui retourne un nombre configurable
de recommandations fictives. Elle sert de base avant l'intégration du vrai
moteur de recommandation.
"""

from typing import Any

from fastapi import FastAPI, Query


app = FastAPI()


'''
Un décorateur est habituellement une fonction qui en prend une autre en argument
et retourne une fonction wrapper

Dans  FastAPI (et d'autre frameworks web)
les décorateurs comme @app.get("/") fonctionnent un peu différement

1. L'enregistrement plutôt que la modification
le décorateur de FastAPI ne cherche pas à "emballer" une fonction pour en modifier le comportement
Son rôle principal est l'enregistrement.

@app.get("/..."), FastAPI ajoute get_recommendations() à un dictionnaire interne
une sorte de "table de routage"

Dit au serveur : "Si on requete l'URL /recommandations/123 avec la méthode GET
exécute cette fonction."
Le wrapper est géré en interne par FastAPI au moment où la requête arrive

1) Inspection : FastAPI regarde les arguments de la fonction (comme user_id: int).
2) Validation : utilise Pydantic pour vérifier que user_id est bien un entier.
3) Exécution : appelle la fonction.
'''

@app.get("/recommandations/{user_id}")
def get_recommendations(
    user_id: int,
    limit: int = Query(10, ge=1, le=100),
) -> dict[str, Any]:
    """Retourne des recommandations fictives pour un utilisateur donné.

    Le paramètre ``limit`` permet de contrôler le nombre de résultats renvoyés.
    Par défaut, l'API retourne 10 recommandations.
    """
    recommendations = [
        {
            "movie_id": movie_id,
            "title": f"Movie {movie_id}",
            "score": round(5.0 - (movie_id - 1) * 0.2, 2),
        }
        for movie_id in range(1, limit + 1)
    ]
    return {"user_id": user_id, "recommendations": recommendations}