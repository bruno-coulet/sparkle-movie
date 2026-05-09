#!/bin/bash

# Script de lancement de l'API FastAPI et du frontend Streamlit
# Usage: bash run.sh

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Activer l'environnement virtuel
source .venv/bin/activate

echo "🚀 Démarrage de Sparkle Movie..."
echo "=================================="

# Nettoyer les ports avant de démarrer
echo "🔧 Nettoyage des ports 8000 et 8501..."
lsof -ti:8000,8501 | xargs kill -9 2>/dev/null || true
sleep 2

# Lancer l'API en arrière-plan
echo "🔥 Lancement de l'API FastAPI..."
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000 > /tmp/api.log 2>&1 &
API_PID=$!
sleep 3

# Vérifier que l'API a démarré
if ! kill -0 $API_PID 2>/dev/null; then
    echo "❌ L'API n'a pas pu démarrer."
    cat /tmp/api.log
    exit 1
fi
echo "✅ API lancée sur http://localhost:8000"
echo "📖 Documentation : http://localhost:8000/docs"

# Lancer Streamlit en arrière-plan
echo ""
echo "🎬 Lancement du frontend Streamlit..."
streamlit run frontend/app.py --logger.level=info > /tmp/streamlit.log 2>&1 &
STREAMLIT_PID=$!
sleep 3

if ! kill -0 $STREAMLIT_PID 2>/dev/null; then
    echo "❌ Streamlit n'a pas pu démarrer. Vérifiez les erreurs ci-dessus."
    cat /tmp/streamlit.log
    kill $API_PID
    exit 1
fi
echo "✅ Frontend lancé sur http://localhost:8501"

echo ""
echo "=================================="
echo "🎉 Tous les services sont en cours d'exécution!"
echo "=================================="
echo ""
echo "📋 Services disponibles :"
echo "  - API: http://localhost:8000"
echo "  - Docs API: http://localhost:8000/docs"
echo "  - Frontend: http://localhost:8501"
echo ""
echo "Appuyez sur Ctrl+C pour arrêter tous les services."
echo ""

# Garder les processus actifs
wait
