"""Build the redistributable sample included in this repo.

The full Kaggle/ULB file (284,807 rows, ~150MB) exceeds GitHub's file-size
limit, so the repo ships a stratified sample instead: every fraud row plus a
seeded random 20,000 legitimate rows. The dataset's DbCL v1.0 license
permits redistribution with attribution (see data-sources.md).

Rates computed on the sample overstate the fraud share by construction
(that is what stratification does) — the sample exists so the project can
be reviewed and run without a 150MB download, and every sample-based number
is labeled as such.
"""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "creditcard.csv"
OUT = ROOT / "data" / "sample" / "creditcard_sample.csv"
N_LEGIT = 20_000
SEED = 42


def main() -> None:
    df = pd.read_csv(RAW)
    frauds = df[df["Class"] == 1]
    legit = df[df["Class"] == 0].sample(n=N_LEGIT, random_state=SEED)
    sample = (
        pd.concat([frauds, legit])
        .sort_values("Time")
        .reset_index(drop=True)
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    sample.to_csv(OUT, index=False)
    print(f"{OUT.name}: {len(sample):,} rows "
          f"({len(frauds)} frauds + {N_LEGIT:,} legitimate), "
          f"{OUT.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
