# Strategy Summary

This project treats fraud detection as a risk strategy problem, not just a
classification exercise. In the Kaggle/ULB sample, fraud is only
0.173% of transactions (492
frauds out of 284,807), which makes accuracy misleading.

The selected model is **Tree model with Random oversampling fallback** with holdout PR-AUC
0.845. Under the default cost model,
the cost-balanced threshold flags 0.19%
of transactions and produces $14,543
in net savings per 100,000 scored transactions.

The recommended deployment is tiered: auto-decline only the highest-risk band,
route the middle-risk band to review or step-up authentication, and monitor
the rest for drift. The headline numbers should be re-cut with issuer-specific
false-positive costs, review capacity, and current fraud controls before a
production decision.
