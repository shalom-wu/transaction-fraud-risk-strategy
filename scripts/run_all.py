"""Run the full reproducible analysis pipeline."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run(script: str) -> None:
    subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts" / script)], check=True)


def main() -> None:
    run("download_data.py")
    run("run_eda.py")
    run("run_modeling.py")
    run("build_deck.py")
    run("make_notebook.py")


if __name__ == "__main__":
    main()

