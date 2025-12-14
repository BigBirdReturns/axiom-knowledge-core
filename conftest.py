import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Add editable-style paths for tests without requiring pip install -e.
for p in [
    ROOT / "packages" / "axm" / "src",
    ROOT / "packages" / "axiom-knowledge-core" / "src",
    ROOT / "apps",
]:
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)
