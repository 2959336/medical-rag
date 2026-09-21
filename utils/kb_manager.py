import os
import shutil
from typing import List, Optional

KB_DIR = "./medical_kb"
TEMP_DIR = "./temp_upload"


def ensure_dirs():
    for d in [KB_DIR, TEMP_DIR]:
        if not os.path.exists(d):
            os.makedirs(d)


def list_kb_files() -> List[str]:
    ensure_dirs()
    files = []
    for root, _, filenames in os.walk(KB_DIR):
        for f in filenames:
            files.append(os.path.join(root, f))
    return files


def add_kb_file(uploaded_file) -> str:
    ensure_dirs()
    path = os.path.join(KB_DIR, uploaded_file.name)
    with open(path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return path


def clear_kb():
    ensure_dirs()
    for item in os.listdir(KB_DIR):
        item_path = os.path.join(KB_DIR, item)
        if os.path.isfile(item_path):
            os.remove(item_path)
        elif os.path.isdir(item_path):
            shutil.rmtree(item_path)


def add_temp_file(uploaded_file) -> str:
    ensure_dirs()
    path = os.path.join(TEMP_DIR, uploaded_file.name)
    with open(path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return path


def clear_temp_files(exclude: Optional[List[str]] = None):
    ensure_dirs()
    exclude = exclude or []
    for item in os.listdir(TEMP_DIR):
        item_path = os.path.join(TEMP_DIR, item)
        if item_path in exclude:
            continue
        if os.path.isfile(item_path):
            os.remove(item_path)
        elif os.path.isdir(item_path):
            shutil.rmtree(item_path)


def get_kb_stats() -> dict:
    ensure_dirs()
    files = list_kb_files()
    total_size = sum(os.path.getsize(f) for f in files if os.path.isfile(f))
    return {
        "doc_count": len(files),
        "total_size_mb": round(total_size / (1024 * 1024), 2),
    }
