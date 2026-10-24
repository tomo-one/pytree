"""Start ohne Installation:  python3 start.py [pfad]

Benötigt nur textual (`python3 -m pip install --user textual`).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from pytree.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
