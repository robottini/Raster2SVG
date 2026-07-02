import PyInstaller.__main__
import os
import shutil

# Pulizia build precedenti
if os.path.exists("build"):
    shutil.rmtree("build")
if os.path.exists("dist"):
    shutil.rmtree("dist")

# Definizione import nascosti necessari per uvicorn, fastapi e sklearn
hidden_imports = [
    # Uvicorn e componenti server
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    # FastAPI e dipendenze base
    'fastapi',
    'starlette',
    'pydantic',
    # Sklearn (spesso problematico con PyInstaller)
    'sklearn.utils._cython_blas',
    'sklearn.neighbors.typedefs',
    'sklearn.neighbors.quad_tree',
    'sklearn.tree._utils',
    'sklearn.utils.sparsetools',
    'sklearn.metrics._pairwise_fast',
]

# Costruzione argomenti PyInstaller
args = [
    'desktop_main.py',           # Script di avvio desktop
    '--name=RasterSVG',          # Nome dell'eseguibile finale
    '--onedir',                  # Crea una cartella (più veloce all'avvio su macOS)
    '--windowed',                # Niente finestra console (macOS .app bundle)
    '--add-data=frontend:frontend',  # Includi la cartella frontend nell'eseguibile
    '--clean',                   # Pulisci la cache di build
    '--noconfirm',               # Sovrascrivi senza chiedere
]

# Aggiungi gli import nascosti
for hidden in hidden_imports:
    args.append(f'--hidden-import={hidden}')

# Esegui PyInstaller
print("Inizio creazione applicazione desktop con PyInstaller...")
PyInstaller.__main__.run(args)
print("\nCreazione completata! L'applicazione si trova nella cartella 'dist'.")
