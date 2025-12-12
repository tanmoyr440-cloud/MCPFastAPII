import os
import base64

# Configuration
PROJECT_ROOT = "."
OUTPUT_FILE = "install_project.py"
EXCLUDED_DIRS = {
    ".git", ".venv", "__pycache__", ".pytest_cache", "backend.egg-info", 
    "logs", "uploads", "data", "node_modules", ".idea", ".vscode"
}
EXCLUDED_FILES = {
    "ai_desk.db", "install_project.py", "generate_installer.py", ".DS_Store", "uv.lock"
}
# Extensions to treat as text (others will be base64 encoded)
TEXT_EXTENSIONS = {
    ".py", ".md", ".txt", ".json", ".toml", ".yaml", ".yml", ".env", ".ini", ".css", ".html", ".js", ".ts", ".tsx", ".jsx"
}

def is_text_file(filename):
    return any(filename.endswith(ext) for ext in TEXT_EXTENSIONS)

def generate_installer():
    print(f"Scanning directory: {os.path.abspath(PROJECT_ROOT)}")
    
    files_data = {}
    
    for root, dirs, files in os.walk(PROJECT_ROOT):
        # Modify dirs in-place to skip excluded directories
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        
        for file in files:
            if file in EXCLUDED_FILES:
                continue
                
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, PROJECT_ROOT)
            
            # Skip if file is in an excluded directory (double check)
            if any(part in EXCLUDED_DIRS for part in rel_path.split(os.sep)):
                continue

            try:
                if is_text_file(file):
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    files_data[rel_path] = {"type": "text", "content": content}
                else:
                    # Binary file
                    with open(file_path, "rb") as f:
                        content = f.read()
                    b64_content = base64.b64encode(content).decode("utf-8")
                    files_data[rel_path] = {"type": "binary", "content": b64_content}
                
                print(f"Included: {rel_path}")
            except Exception as e:
                print(f"Skipping {rel_path}: {e}")

    # Generate the installer script content
    installer_content = f"""import os
import base64
import sys

FILES = {repr(files_data)}

def create_project():
    print("Recreating project structure...")
    
    for path, data in FILES.items():
        # Ensure directory exists
        dir_name = os.path.dirname(path)
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)
            
        try:
            if data["type"] == "text":
                with open(path, "w", encoding="utf-8") as f:
                    f.write(data["content"])
            else:
                with open(path, "wb") as f:
                    f.write(base64.b64decode(data["content"]))
            print(f"Created: {{path}}")
        except Exception as e:
            print(f"Error creating {{path}}: {{e}}")

    print("\\nProject recreation complete!")

if __name__ == "__main__":
    create_project()
"""

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(installer_content)
    
    print(f"\nSuccessfully generated '{OUTPUT_FILE}'.")
    print(f"Run 'python {OUTPUT_FILE}' in a new directory to recreate the project.")

if __name__ == "__main__":
    generate_installer()
