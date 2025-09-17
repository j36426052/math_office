import sys, pathlib

# Ensure project root (one level up from 'backend') is on path so 'backend.app' imports work
root = pathlib.Path(__file__).resolve().parents[2]
if str(root) not in sys.path:
    sys.path.insert(0, str(root))