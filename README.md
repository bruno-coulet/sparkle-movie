# Algo de recommandations sparkle movie

## Vous travaillez pour une plateforme de streaming vidéo

**Objectif** : Améliorer l'expérience utilisateur en proposant des recommandations personnalisées.  

Vous devez utiliser l'ensemble de données MovieLens pour
créer un modèle de recommandation et fournir une liste de films
recommandés pour différents utilisateurs.


## Setup WSL
1. Système et Java

``` shell
sudo apt update && sudo apt upgrade -y
sudo apt install openjdk-17-jdk unzip -y
java -version
```
2. Installation de uv (Gestionnaire Python)
C'est l'outil de gestion d'environnement.   
Sous Linux, on l'installe généralement via leur script officiel :

```shell
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env  # Pour activer la commande 'uv' immédiatement
``` 

3. Git et Sécurité (Le pont vers GitHub)
```shell
# Configuration de l'identité
git config --global user.email "..."
git config --global user.name "..."

# Génération de la clé
ssh-keygen -t ed25519 -C "..."
# (Ici, copier le contenu de ~/.ssh/id_ed25519.pub sur GitHub)

# Bascule du dépôt existant vers SSH
git remote set-url origin git@github.com:bruno-coulet/sparkle-movie.git

git config --global user.email "..."
git config --global user.name "..."
``` 


4. Structure du Projet et Données

```shell
mkdir -p data/raw/small data/processed src
cd data/raw/small
wget https://files.grouplens.org/datasets/movielens/ml-latest-small.zip
# installer l'outil pour dezipper
sudo apt update && sudo apt install unzip
# Dézipper
unzip ml-latest-small.zip
# On déplace le contenu du dossier extrait vers le dossier courant (.)
mv ml-latest-small/* .
# suprime le fichier zip
rm -rf ml-latest-small.zip
# Revenir à la racine du projet
cd ../../..
```

5. Environnement Python avec uv

```shell
uv venv                       # Créer l'environnement
source .venv/bin/activate     # L'activer
uv add pyspark                # Installer les dépendances
```







### Le dataset contient les informations suivantes :
1. ratings.csv : Les notes attribuées par les utilisateurs aux films.
○ **userId, movieId, rating, timestamp**

2. movies.csv : Les métadonnées des films.
○ **movieId, title, genres**

1. Préparation de l’environnement
● Installez PySpark sur votre machine. (une API Python pour Spark)
● Configurez une session Spark.
● Récupérez le dataset [MovieLens](https://grouplens.org/datasets/movielens/),   
différentes tailles sont disponibles selon les ressources.


### 2. Chargement et exploration des données
● Importez les fichiers ratings.csv et movies.csv dans des DataFrames
Spark.
● Affichez les 10 premières lignes de chaque DataFrame pour en
comprendre la structure.
● Nettoyez les données si nécessaire (valeurs manquantes, doublons,
etc.).
● Analysez les tendances générales :
○ Quels sont les films les mieux notés en moyenne ?
○ Quels genres de films sont les plus populaires ?
● Générez différentes visualisations à l’aide de librairies Python ainsi que
l’outil Tableau Desktop.

### 3. Modélisation avec Spark MLlib : ALS

**MLlib** est un wrapper pour PySpark et la bibliothèque de machine learning de Spark.
Cette bibliothèque utilise la technique du parallélisme des données pour stocker et exploiter les données. L'API de machine learning fournie par la bibliothèque MLlib est assez simple à utiliser. MLlib prend en charge de nombreux algorithmes de machine learning pour la classification, la régression, le clustering, le filtrage collaboratif, la réduction de dimensionnalité et l'identification des primitives d'optimisation sous-jacentes.

● Utilisez l’algorithme ALS (Alternating Least Squares matrix factorization)
de Spark MLlib pour entraîner un modèle de recommandation.

● Ajustez les hyperparamètres comme le rank, la régularisation
(regParam) et le nombre d’itérations.

● Utilisez des métriques comme la Root Mean Square Error (RMSE) pour
évaluer la performance du modèle.


### 4. Recommandation basée sur le contenu
● Créez des profils de films basés sur les genres.
● Implémentez un système recommandant des films similaires à ceux
aimés par un utilisateur (TF-IDF, similarité cosinus).
5. Recommandation Basée sur les Proximités Utilisateurs (KNN)
● Implémentez une approche KNN pour trouver des utilisateurs similaires.
● Générez des recommandations en fonction des évaluations des voisins
proches.


### 6. Evaluation des approches de recommandation
● Évaluez la précision et la couverture des recommandations.
● Comparez les résultats des différentes approches.
● Donnez des recommandations pour 3 à 5 utilisateurs fictifs.
● Concluez sur la performance de vos différentes méthodes.
