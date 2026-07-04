# Data Quality and Exploratory Notes

## Source file

- Path: `data/raw/creditcard.csv`
- Rows: 284,807
- Columns: 31
- Missing cells: 0
- Exact duplicate rows: 1,081
- Dataset time span: 2.00 elapsed days

## Class imbalance

Fraud accounts for **0.173%** of transactions. This is the
central modeling and business issue: a classifier can be more than 99% accurate
while catching no fraud at all, and a threshold that catches more fraud can
still be economically bad if it blocks too many legitimate customers.

| class | label | transactions | share |
| --- | --- | --- | --- |
| 0 | Legitimate | 284315 | 99.827% |
| 1 | Fraud | 492 | 0.173% |

## Amount distribution

The fraud class has a different amount profile, but amount alone is not enough
to explain the model. The V1-V28 columns are PCA-anonymized, so feature-level
interpretation is intentionally limited.

| class | label | transactions | mean_amount | median_amount | total_amount | max_amount |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | Legitimate | 284315 | $88.29 | $22.00 | $25,102,462.04 | $25,691.16 |
| 1 | Fraud | 492 | $122.21 | $9.25 | $60,127.97 | $2,125.87 |

## Time pattern caveat

`Time` is seconds elapsed since the first transaction in the dataset. The
project derives `relative_hour = floor(Time / 3600) mod 24`, but this is a
relative elapsed-hour pattern, not an actual customer local time-of-day.
