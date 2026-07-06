# Dashboard Brief - Transaction Fraud Risk

## Audience and purpose

This dashboard is for a fraud operations, risk analytics, or payments strategy reviewer. It should show how threshold choice changes fraud capture, review load, and cost.

## Pages

### 1 - Executive KPI

Cards for transaction count, fraud rate, model PR-AUC, recommended threshold, alert rate, and net savings per 100K transactions.

### 2 - Diagnostic Analysis

Show fraud by amount band, elapsed hour, class balance, and precision-recall tradeoff.

### 3 - Decision Support

Rank thresholds by expected net savings and compare conservative, cost-balanced, and aggressive review scenarios.

## Honesty notes

The dataset is anonymized and PCA-transformed. It supports operating-threshold analysis, not merchant/customer behavioral explanations.
