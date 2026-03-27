import os
import zipfile

def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        # Ignorar pastas desnecessárias
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'venv', 'node_modules', '.gemini', 'tmp']]
        for file in files:
            if file.endswith('.zip') or file.endswith('.db') or file.endswith('.sqlite3') or file.endswith('.env'):
                continue
            file_path = os.path.join(root, file)
            ziph.write(file_path, os.path.relpath(file_path, path))

if __name__ == '__main__':
    source_dir = r"c:\Users\User\Documents\BorgesOS_Atualizado"
    zip_path = os.path.join(source_dir, "borges.zip")
    
    print("Compactando código fonte...")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipdir(source_dir, zipf)
    print(f"Compactação concluída: {zip_path}")
