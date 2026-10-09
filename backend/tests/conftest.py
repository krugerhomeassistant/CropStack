import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["CROPSTACK_DATA_DIR"] = tempfile.mkdtemp()
os.environ["CROPSTACK_STATIC_DIR"] = "/nonexistent"
# API tests use a small fixture catalog with invented values; test_catalog.py also loads the real catalog/.
os.environ["CROPSTACK_CATALOG_DIR"] = str(Path(__file__).parent / "fixtures" / "catalog")
os.environ["CROPSTACK_SCHEDULER"] = "false"  # never call outside services from tests
