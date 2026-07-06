# Refresh Instructions

```bash
python scripts/run_all.py
python scripts/run_sql.py
```

The SQL runner uses the full raw file when `data/raw/creditcard.csv` exists and falls back to the included stratified sample otherwise. After regenerating `data/powerbi/`, open the manually built `.pbix`, confirm CSV paths, and use Home -> Refresh.
