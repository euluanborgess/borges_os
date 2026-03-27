import os
import zipfile

def zipdir(path, ziph, exclude_dirs, exclude_exts):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        # Exclude directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for file in files:
            ext = os.path.splitext(file)[1]
            if ext not in exclude_exts and file != "borges.zip":
                filepath = os.path.join(root, file)
                arcname = os.path.relpath(filepath, path)
                ziph.write(filepath, arcname)

if __name__ == '__main__':
    project_dir = "c:/Users/User/Documents/BorgesOS_Atualizado"
    zip_path = os.path.join(project_dir, "borges.zip")
    
    exclude_dirs = {
        '.git', '.venv', 'venv', '__pycache__', 'node_modules', '.gemini', '.idea', '.vscode'
    }
    exclude_exts = {'.pyc'}

    print("Zipping the project folder to borges.zip...")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipdir(project_dir, zipf, exclude_dirs, exclude_exts)
    
    size_mb = os.path.getsize(zip_path) / (1024 * 1024)
    print(f"Zip created: {zip_path} ({size_mb:.2f} MB)")
