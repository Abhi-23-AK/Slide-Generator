import os
import re

search_terms = [
    r"_render_arch_matplotlib",
    r"cairosvg\.svg2png",
    r"inkscape",
    r"DIAGRAM_CACHE",
    r"generate_architecture_xml_prompt",
    r"generate_architecture_v4",
    r"cell_count"
]

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
                    for term in search_terms:
                        if re.search(term, content):
                            results.append((term, path))
            except Exception as e:
                pass

for term, path in results:
    print(f"Term: {term} found in: {path}")
