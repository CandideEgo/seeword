"""Keep the consistency suite importable without ``backend/`` on ``sys.path``.

CI runs this directory with ``-o pythonpath=`` so the installed wheel, not
``backend/slcs``, is the package under test. ``--import-mode=importlib`` then
inserts nothing, so the stdio test's sibling import needs this path entry.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
