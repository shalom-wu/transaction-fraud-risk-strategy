-- ============================================================================
-- data_quality_checks.sql — validation gate for the transactions table
-- Each check returns: check_name | records_flagged | detail
-- Runs against the full raw file when present, else the included sample
-- (see meta.data_basis).
-- ============================================================================

SELECT '01 missing values in any used column' AS check_name,
       COUNT(*) FILTER (WHERE Time IS NULL OR Amount IS NULL OR Class IS NULL) AS records_flagged,
       'the ULB file is famously complete — expect 0' AS detail
FROM transactions

UNION ALL
SELECT '02 class label outside {0,1}',
       COUNT(*) FILTER (WHERE Class NOT IN (0, 1)),
       'binary fraud label'
FROM transactions

UNION ALL
SELECT '03 negative transaction amounts',
       COUNT(*) FILTER (WHERE Amount < 0),
       'amounts must be non-negative'
FROM transactions

UNION ALL
SELECT '04 exact duplicate rows (README: 1,081 on the full file)',
       COUNT(*) - (SELECT COUNT(*) FROM (SELECT DISTINCT * FROM transactions)),
       'documented, not dropped — repeated-looking records can be business-real in payments'
FROM transactions

UNION ALL
SELECT '05 Time outside the two-day capture window (0-172,800s)',
       COUNT(*) FILTER (WHERE Time < 0 OR Time > 172800),
       'Time is seconds since first transaction'
FROM transactions

UNION ALL
SELECT '06 zero-amount transactions (share sanity, not an error)',
       COUNT(*) FILTER (WHERE Amount = 0),
       'zero-amount authorizations exist in card data; kept'
FROM transactions

ORDER BY check_name;
