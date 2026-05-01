import sys
from pathlib import Path

# Ensure the repo root is on sys.path so `from backend.app...` imports
# resolve correctly in both local runs and GitHub Actions CI.
sys.path.insert(0, str(Path(__file__).parent))