#!/bin/bash

# Ottieni la directory in cui si trova lo script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Nome della directory dell'ambiente virtuale
VENV_DIR="venv"

echo "=========================================="
echo "   Avvio di RasterSVG in corso..."
echo "   NON CHIUDERE QUESTA FINESTRA"
echo "   fino a quando non hai finito di usare l'app."
echo "=========================================="
echo ""

# 1. Controlla e gestisci l'ambiente virtuale
if [ -d "$VENV_DIR" ]; then
    # Verifica se l'ambiente virtuale è valido per la posizione corrente
    # Se la cartella è stata spostata, python3 all'interno del venv fallirà
    if ! "$VENV_DIR/bin/python3" -c "exit()" 2>/dev/null; then
        echo "Rilevato spostamento della cartella. Rigenerazione ambiente..."
        rm -rf "$VENV_DIR"
    fi
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "Configurazione iniziale (può richiedere qualche minuto)..."
    python3 -m venv $VENV_DIR
fi

# 2. Attiva l'ambiente virtuale
source $VENV_DIR/bin/activate

# 3. Installa le dipendenze
if [ -f "requirements.txt" ]; then
    echo "Verifica aggiornamenti dipendenze..."
    pip install -r requirements.txt > /dev/null 2>&1
fi

# 4. Funzione per aprire il browser con controllo disponibilità
open_browser() {
    echo "In attesa che il server sia pronto..."
    # Tenta di connettersi per 30 secondi
    for i in {1..30}; do
        # Controlla se il server risponde (sopprimendo output errori)
        if curl -s http://localhost:8000 > /dev/null; then
            echo "Server pronto! Apertura browser..."
            open "http://localhost:8000"
            return
        fi
        sleep 1
    done
    
    # Se dopo 30 secondi non risponde, prova comunque ad aprire
    echo "Il server sta impiegando più del previsto. Apro comunque il browser..."
    open "http://localhost:8000"
}

# Avvia l'apertura del browser in background
open_browser &

# 5. Avvia il server
echo "Server avviato. Vai al browser!"
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

# Quando uvicorn termina (Ctrl+C)
echo ""
echo "Applicazione terminata."
