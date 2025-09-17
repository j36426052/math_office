import sys
from pathlib import Path

tests_dir = Path(__file__).resolve().parent
backend_dir = tests_dir.parent  # backend/
project_root = backend_dir.parent  # project root containing backend/

for p in (backend_dir, project_root):
    p_str = str(p)
    if p_str not in sys.path:
        sys.path.insert(0, p_str)