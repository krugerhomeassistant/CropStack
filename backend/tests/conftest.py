import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["CROPSTACK_DATA_DIR"] = tempfile.mkdtemp()
os.environ["CROPSTACK_STATIC_DIR"] = "/nonexistent"
