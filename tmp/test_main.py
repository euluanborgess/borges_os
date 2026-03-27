import sys
import os
import traceback

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    import main
    print("Main importado com sucesso!")
except Exception as e:
    print("ERRO FATAL AO IMPORTAR MAIN:")
    traceback.print_exc()
