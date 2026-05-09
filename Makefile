.PHONY: help install clean prepare train run frontend api stop docs

# Variables
PYTHON := python
PROJECT_NAME := sparkle-movie
VENV := .venv

help:
	@echo "=================================================================="
	@echo "$(PROJECT_NAME) - Commandes disponibles"
	@echo "=================================================================="
	@echo ""
	@echo "Setup et Installation:"
	@echo "  make install          Installe les dépendances Python"
	@echo "  make clean            Supprime les fichiers temporaires"
	@echo ""
	@echo "Données et Modèle ML:"
	@echo "  make prepare          Convertit CSV → Parquet"
	@echo "  make train            Entraîne le modèle ALS"
	@echo "  make ml               Exécute prepare + train"
	@echo ""
	@echo "Développement:"
	@echo "  make api              Lance l'API FastAPI (port 8000)"
	@echo "  make frontend         Lance l'interface Streamlit (port 8501)"
	@echo "  make run              Lance API et Streamlit (sequential)"
	@echo ""
	@echo "Utilitaires:"
	@echo "  make stop             Arrête les ports 8000 et 8501"
	@echo "  make docs             Ouvre la doc Swagger"
	@echo ""
	@echo "=================================================================="

# ============================================================================
# INSTALLATION ET SETUP
# ============================================================================

install:
	@echo "📦 Installation des dépendances..."
	uv sync
	@echo "✅ Dépendances installées"

clean:
	@echo "🧹 Nettoyage des fichiers temporaires..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name ".DS_Store" -delete 2>/dev/null || true
	@echo "✅ Nettoyage terminé"

# ============================================================================
# DONNÉES ET ML
# ============================================================================

prepare:
	@echo "📊 Préparation des données (CSV → Parquet)..."
	$(PYTHON) src/preprocess.py
	@echo "✅ Données préparées"

train:
	@echo "🤖 Entraînement du modèle ALS..."
	$(PYTHON) src/train.py
	@echo "✅ Modèle entraîné"

ml: prepare train
	@echo "✅ Pipeline ML complète"

# ============================================================================
# DÉVELOPPEMENT
# ============================================================================

api:
	@echo "🚀 Lancement de l'API FastAPI sur http://localhost:8000"
	uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

frontend:
	@echo "🎨 Lancement de Streamlit sur http://localhost:8501"
	streamlit run streamlit/app.py --logger.level=info

run: stop
	@echo "🔥 Démarrage du système complet..."
	@echo "   - API: http://localhost:8000/docs"
	@echo "   - Frontend: http://localhost:8501"
	@echo ""
	@echo "Conseil: Ouvrez deux terminaux - l'un pour 'make api' et l'autre pour 'make frontend'"
	@echo ""

# ============================================================================
# UTILITAIRES
# ============================================================================

stop:
	@echo "🛑 Arrêt des services..."
	@lsof -i :8000 | grep LISTEN | awk '{print $$2}' | xargs kill -9 2>/dev/null || true
	@lsof -i :8501 | grep LISTEN | awk '{print $$2}' | xargs kill -9 2>/dev/null || true
	@sleep 1
	@echo "✅ Services arrêtés"

docs:
	@echo "📚 Ouverture de la documentation Swagger..."
	open http://localhost:8000/docs || xdg-open http://localhost:8000/docs || true
