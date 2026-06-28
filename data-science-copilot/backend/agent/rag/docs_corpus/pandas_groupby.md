# Pandas: GroupBy and Aggregation

`df.groupby("col")` splits the DataFrame by the unique values of `col`. Chain an aggregation:
`df.groupby("region")["revenue"].sum()`, or aggregate multiple columns differently with
`.agg({"revenue": "sum", "orders": "mean"})`. `df.groupby(["a", "b"])` groups by multiple keys
and returns a MultiIndex result; call `.reset_index()` to flatten it back into plain columns
(useful before plotting or returning a tidy `result` table).

`groupby(...).size()` counts rows per group (works on any dtype); `groupby(...).count()` counts
non-null values per column per group. `.nunique()` counts distinct values per group.

For "auto-segment customers by spend" style cohort analysis, a common pattern is to bucket a
numeric column with `pd.qcut(df["spend"], q=4, labels=["Low", "Mid", "High", "Top"])` (equal-sized
quantile bins) or `pd.cut(df["spend"], bins=[...])` (custom fixed-width bins), assign the result
to a new column, then `groupby` on that new column.

Common errors:
- `TypeError`/`DataError: No numeric types to aggregate` -- you called `.sum()`/`.mean()` on a
  group that includes non-numeric (string/object) columns. Select numeric columns first:
  `df.groupby("col")[numeric_cols].sum()`, or pass `numeric_only=True` to the aggregation call.
- `KeyError` after groupby+agg with a dict -- the column name you referenced doesn't exist in
  the *original* frame; check spelling/whitespace before grouping.
- Forgetting `as_index=False` or `.reset_index()` leads to the group key becoming the index,
  which then silently disappears from `to_dict(orient="records")` output -- always
  `reset_index()` before serializing a groupby result as a table.
- `pd.qcut` raises `ValueError: Bin edges must be unique` when a column has too many repeated
  values for the requested number of quantiles; reduce `q` or use `duplicates="drop"`.
