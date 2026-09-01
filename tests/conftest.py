import sys
from pathlib import Path

# Make the `ai` package importable so that the wrapper test modules under
# tests/ (e.g. test_ai_chunking.py) can import from `ai.tests.*`.
sys.path.insert(0, str(Path(__file__).parents[1]))
