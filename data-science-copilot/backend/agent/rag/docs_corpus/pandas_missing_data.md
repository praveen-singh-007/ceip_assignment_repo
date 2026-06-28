# Pandas: Working with Missing Data

Pandas represents missing values as `NaN` (float), `None`, `pd.NaT` (for datetimes), or `pd.NA`.
Use `df.isna()` / `df.isnull()` to get a boolean mask, and `df.notna()` for the inverse. Never
compare directly to `NaN` with `==` -- `NaN == NaN` is always `False`; always use `isna()`.

`df.dropna()` drops rows (default `axis=0`) containing any NaN. Pass `subset=["col"]` to only
consider specific columns, and `how="all"` to require every value in the row/column to be NaN
before dropping. `df.dropna(thresh=N)` keeps rows with at least N non-null values.

`df.fillna(value)` fills missing values. `value` can be a scalar, a dict mapping column name to
fill value, or a Series. Use `method="ffill"` (forward fill) or `method="bfill"` (backward fill)
for time-ordered data. `df["col"].fillna(df["col"].mean())` is a common pattern for numeric
imputation.

Common errors:
- `TypeError: boolean value of NA is ambiguous` happens when a NA-containing boolean Series is
  used in an `if` statement or Python `and`/`or`. Use `.any()`, `.all()`, or `.fillna(False)`
  first.
- Arithmetic with NaN propagates NaN (`1 + np.nan == nan`), it does not raise. If you expect an
  exception and don't get one, check for silent NaN propagation with `df.isna().sum()`.
- `df["col"].mean()` and similar aggregations skip NaN by default (`skipna=True`), so a column
  that is "all NaN" returns NaN, not an error.

To count missing values per column for a data-quality report: `df.isna().sum()`. To get the
percentage: `df.isna().mean() * 100`. To find fully duplicated missing-value rows combined with
`duplicated()`, see the duplicates documentation.
