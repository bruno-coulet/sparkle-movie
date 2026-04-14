from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any


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
def get_recommendations(user_id: int) -> dict[str, Any]:
    # Placeholder pour les recommandations basées sur le modèle
    recommendations = [
        {"movie_id": 1, "title": "Movie A", "score": 4.5},
        {"movie_id": 2, "title": "Movie B", "score": 4.0},
        {"movie_id": 3, "title": "Movie C", "score": 3.5},
    ]
    return {"user_id": user_id, "recommendations": recommendations}