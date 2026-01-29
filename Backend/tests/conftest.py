# tests/conftest.py
import os
import sys

# project root = one level up from tests/ directory
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
