import os
import hashlib
import json
import zipfile

def get_hash(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def build_package():
    manifest = {"commit": "HEAD", "files": []}
    
    exclude_dirs = [".venv", ".git", "__pycache__", "output/smoke_models", "output/smoke_eval", "output/smoke_scoring"]
    
    with zipfile.ZipFile('PerformanceMonitoring_Agent_20260824.zip', 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk('.'):
            dirs[:] = [d for d in dirs if not any(x in os.path.join(root, d) for x in exclude_dirs)]
            for file in files:
                if file.endswith('.zip') or file == "SUBMISSION_MANIFEST.json":
                    continue
                filepath = os.path.join(root, file)
                arcname = os.path.relpath(filepath, '.')
                zipf.write(filepath, arcname)
                manifest["files"].append({"path": arcname, "sha256": get_hash(filepath)})
                
    with open("SUBMISSION_MANIFEST.json", "w") as f:
        json.dump(manifest, f, indent=2)
        
    print("Package and manifest created.")

if __name__ == "__main__":
    build_package()
