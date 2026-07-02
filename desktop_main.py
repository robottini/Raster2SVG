import sys
import os
import threading
import base64
import uvicorn
import webview

# Aggiungiamo la directory corrente al path per poter importare backend
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.main import app

class Api:
    def __init__(self):
        self.original_file_path = None

    def open_image(self):
        file_types = ('Image Files (*.png;*.jpg;*.jpeg;*.bmp;*.webp)', 'All files (*.*)')
        result = webview.windows[0].create_file_dialog(webview.OPEN_DIALOG, allow_multiple=False, file_types=file_types)
        
        if result and len(result) > 0:
            file_path = result[0]
            self.original_file_path = file_path
            
            try:
                with open(file_path, 'rb') as f:
                    content = f.read()
                    b64_content = base64.b64encode(content).decode('utf-8')
                    
                return {
                    'filename': os.path.basename(file_path),
                    'data': b64_content
                }
            except Exception as e:
                print(f"Error opening file: {e}")
                return None
        return None

    def save_svg(self, content, filename=None):
        file_types = ('SVG Files (*.svg)', 'All files (*.*)')
        
        # Determine default path and filename
        initial_directory = ''
        initial_filename = 'converted.svg'
        
        if filename:
             base_name = os.path.splitext(filename)[0]
             initial_filename = f"{base_name}.svg"
             if self.original_file_path:
                 initial_directory = os.path.dirname(self.original_file_path)
        elif self.original_file_path:
            initial_directory = os.path.dirname(self.original_file_path)
            # Get filename without extension and add .svg
            base_name = os.path.splitext(os.path.basename(self.original_file_path))[0]
            initial_filename = f"{base_name}.svg"

        # open save dialog
        filename = webview.windows[0].create_file_dialog(
            webview.SAVE_DIALOG, 
            allow_multiple=False, 
            file_types=file_types, 
            save_filename=initial_filename,
            directory=initial_directory
        )
        
        if filename:
            try:
                # If filename is a tuple/list (some versions), take first element
                if isinstance(filename, (list, tuple)):
                    filename = filename[0]
                    
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True
            except Exception as e:
                print(f"Error saving file: {e}")
        return False

    def close_app(self):
        if webview.windows:
            webview.windows[0].destroy()
        sys.exit()

def start_server():
    # Avvia il server su localhost
    # Usiamo 127.0.0.1 per essere certi che sia accessibile solo localmente
    # log_level="error" per ridurre il rumore nella console
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")

if __name__ == "__main__":
    # Avvia il server in un thread separato
    t = threading.Thread(target=start_server, daemon=True)
    t.start()
    
    api = Api()
    # Crea una finestra nativa che punta al server locale
    webview.create_window("RasterSVG", "http://127.0.0.1:8000", width=1200, height=800, js_api=api)
    
    # Avvia l'interfaccia grafica
    webview.start()
