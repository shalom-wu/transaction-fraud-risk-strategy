# Data Sources

## Primary dataset

- Dataset: Credit Card Fraud Detection
- Source: Kaggle, Machine Learning Group - Universite Libre de Bruxelles
- Kaggle URL: https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud
- Local expected file: `data/raw/creditcard.csv`
- Rows in the downloaded archive used here: 284,807 transactions
- Fraud labels in the downloaded archive used here: 492 frauds
- Feature caveat: `V1` through `V28` are PCA-anonymized fields. The dataset
  does not expose merchant, cardholder, geography, device, or raw behavioral
  features, so this project does not make strong feature-level "why" claims.

## How to reproduce the data setup

1. Download `archive.zip` from the Kaggle page above.
2. Put it anywhere local.
3. Run:

```bash
python scripts/download_data.py --archive path/to/archive.zip
```

The raw CSV is intentionally ignored by git. This keeps the public repository
focused on source attribution, reproducible code, and generated analysis
artifacts rather than redistributing Kaggle data.

## Source limitations

- This is a well-known public benchmark dataset. The project value is not
  claiming a novel fraud dataset or a novel model family.
- `Time` is elapsed seconds since the first transaction, not a timestamp with
  date, timezone, merchant local time, or customer local time.
- `Amount` is available, but the dataset does not expose recovery rates,
  chargeback outcomes, review operations cost, false-decline churn, or current
  rule-stack performance. Those are modeled as explicit assumptions.

