"""Prepare the Kaggle credit card fraud dataset.

Usage examples:
    python scripts/download_data.py --archive C:/Users/shalo/Downloads/archive.zip
    python scripts/download_data.py --check-only
"""

from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from fraud_risk.config import RAW_DATA_PATH  # noqa: E402


def extract_archive(archive_path: Path, output_path: Path) -> None:
    if not archive_path.exists():
        raise FileNotFoundError(f"Archive not found: {archive_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path) as zf:
        candidates = [name for name in zf.namelist() if name.lower().endswith("creditcard.csv")]
        if not candidates:
            raise FileNotFoundError("No creditcard.csv file found inside archive")
        with zf.open(candidates[0]) as source, output_path.open("wb") as target:
            target.write(source.read())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, help="Path to Kaggle archive.zip")
    parser.add_argument("--check-only", action="store_true", help="Only verify whether data/raw/creditcard.csv exists")
    args = parser.parse_args()

    if RAW_DATA_PATH.exists():
        print(f"Found dataset: {RAW_DATA_PATH}")
        return

    if args.check_only:
        raise FileNotFoundError(
            f"Dataset missing: {RAW_DATA_PATH}. Download Kaggle dataset "
            "mlg-ulb/creditcardfraud and place creditcard.csv in data/raw/."
        )

    if args.archive:
        extract_archive(args.archive, RAW_DATA_PATH)
        print(f"Extracted dataset to {RAW_DATA_PATH}")
        return

    raise FileNotFoundError(
        "Dataset is missing. Download from "
        "https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud, then run:\n"
        "python scripts/download_data.py --archive path/to/archive.zip"
    )


if __name__ == "__main__":
    main()

