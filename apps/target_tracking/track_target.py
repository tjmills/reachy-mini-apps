from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent / "src"))

from tracker import main_from_cli

if __name__ == "__main__":
    main_from_cli()
