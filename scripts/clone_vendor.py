"""Clone the upstream Reachy Mini repo into vendor/ for read-only reference.

This is useful for Claude Code context and for inspecting SDK implementation details.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

UPSTREAM = "https://github.com/pollen-robotics/reachy_mini.git"

def main() -> None:
    root = Path(__file__).resolve().parents[1]
    vendor_dir = root / "vendor"
    repo_dir = vendor_dir / "reachy_mini"
    vendor_dir.mkdir(parents=True, exist_ok=True)

    if repo_dir.exists():
        print(f"Already exists: {repo_dir}")
        return

    print(f"Cloning {UPSTREAM} -> {repo_dir}")
    subprocess.check_call(["git", "clone", UPSTREAM, str(repo_dir)])
    print("Done. Note: vendor/ is gitignored.")

if __name__ == "__main__":
    main()
