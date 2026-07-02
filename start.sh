#!/bin/bash

# Ottieni la directory in cui si trova lo script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Nome della directory dell'ambiente virtuale
VENV_DIR="venv"

echo "=== RasterSVG Launcher ==="

# 1. Controlla e crea l'ambiente virtuale se necessario
if [ ! -d "$VENV_DIR" ]; then
    echo "Creazione ambiente virtuale in $VENV_DIR..."
    python3 -m venv $VENV_DIR
fi

# 2. Attiva l'ambiente virtuale
source $VENV_DIR/bin/activate

# 3. Installa le dipendenze
if [ -f "requirements.txt" ]; then
    echo "Controllo dipendenze..."
    pip install -r requirements.txt
fi

# 4. Funzione per aprire il browser
open_browser() {
    sleep 2 # Aspetta che il server si avvii
    echo "Apertura browser..."
    open "http://localhost:8000"
}

# Avvia l'apertura del browser in background
open_browser &

# 5. Avvia il server
echo "Avvio server..."
# Esegui uvicorn dal modulo backend.main
# --reload permette di ricaricare il server se modifichi il codice
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
