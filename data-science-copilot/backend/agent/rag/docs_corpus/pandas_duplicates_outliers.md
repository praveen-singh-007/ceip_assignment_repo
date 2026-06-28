# Pandas: Duplicates and Outlier Detection (Data Quality Audits)

`df.duplicated()` returns a boolean Series marking rows that are exact duplicates of an earlier
row (by default considering *all* columns); pass `subset=["col1", "col2"]` to only consider a
subset of columns, and `keep="first"`/`"last"`/`False` to control which occurrence(s) are
flagged. `df.drop_duplicates(subset=..., keep=...)` removes them. `df.duplicated().sum()` gives a
quick duplicate-row count for a cleanliness report.

For numeric outlier detection, two standard, well-understood approaches:

1. **IQR (interquartile range) method** -- robust to non-normal distributions:
   `q1, q3 = df["col"].quantile([0.25, 0.75])`; `iqr = q3 - q1`; a value is an outlier if it is
   below `q1 - 1.5 * iqr` or above `q3 + 1.5 * iqr`.
2. **Z-score method** -- assumes roughly normal data:
   `z = (df["col"] - df["col"].mean()) / df["col"].std()`; flag `abs(z) > 3` as an outlier.

A full data-quality / cleanliness report typically combines: `df.isna().sum()` (missing values
per column), `df.duplicated().sum()` (duplicate rows), dtype sanity checks (`df.dtypes`), and an
outlier count per numeric column using one of the methods above. Assigning the prose summary of
these findings to the `insights` string is the expected output shape for a "data quality audit"
style question.

Common errors:
- Calling `.quantile()` on a non-numeric column raises `TypeError`; restrict outlier checks to
  `df.select_dtypes(include="number").columns`.
- `std()` (and therefore z-score) on a column with only one unique value is `0`, causing a
  `ZeroDivisionError`-equivalent (`inf`/`NaN` result) -- guard with a check for `std() > 0`
  before computing z-scores.
