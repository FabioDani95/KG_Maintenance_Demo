#!/bin/bash

# Script di avvio per Knowledge Graph Maintenance System

echo "=============================================="
echo "  Knowledge Graph Maintenance System"
echo "=============================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 non trovato. Installare Python 3 prima di continuare."
    exit 1
fi

# Check if dependencies are installed
if ! python3 -c "import flask" 2> /dev/null; then
    echo "📦 Installazione dipendenze..."
    cd backend
    pip install -r requirements.txt
    cd ..
    echo "✅ Dipendenze installate"
    echo ""
fi

echo "🚀 Avvio del backend server..."
echo ""
echo "Il server sarà disponibile su: http://localhost:5000"
echo ""
echo "Per fermare il server, premi CTRL+C"
echo ""
echo "=============================================="
echo ""

cd backend
python3 app.py
