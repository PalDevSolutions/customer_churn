"""Root conftest — makes the project root importable as `src.*` in all tests."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
