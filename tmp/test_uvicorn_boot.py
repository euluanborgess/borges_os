import traceback
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    import uvicorn
    import main
    print("Tentando bind local da porta 8000 via API Uvicorn síncrona...")
    uvicorn.run(main.app, host="127.0.0.1", port=8000, log_level="debug")
except Exception as e:
    print("ERRO FATAL NO STARTUP:", flush=True)
    traceback.print_exc()
