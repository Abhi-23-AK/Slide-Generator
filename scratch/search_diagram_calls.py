import os
import re

results = []
for root, dirs, files in os.walk("."):
    if ".git" in root or "venv" in root or "__pycache__" in root or ".gemini" in root:
        continue
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    if "generate_drawio_diagram" in content:
                        results.append(path)
            except Exception as e:
                pass

for path in results:
    print(f"generate_drawio_diagram found in: {path}")
