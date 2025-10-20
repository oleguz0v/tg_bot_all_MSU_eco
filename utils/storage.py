import json
import os
import tempfile

def load_json(filename, default):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default

def save_json(filename, data):
    # Атомарная запись: сначала записываем во временный файл, затем заменяем
    dir_name = os.path.dirname(filename) or "."
    os.makedirs(dir_name, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", delete=False, dir=dir_name, encoding="utf-8") as tmp:
        json.dump(data, tmp, indent=4, ensure_ascii=False)
        tmp_path = tmp.name
    os.replace(tmp_path, filename)