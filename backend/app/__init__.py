import sys
from pathlib import Path

# Ensure both backend root and workspace root are in sys.path
# so imports like 'backend.app...' and 'app...' both resolve cleanly.
_backend_dir = Path(__file__).resolve().parent.parent
_workspace_dir = _backend_dir.parent

for _p in (str(_backend_dir), str(_workspace_dir)):
    if _p not in sys.path:
        sys.path.insert(0, _p)
