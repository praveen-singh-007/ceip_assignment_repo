# Pandas: Merge, Join and Concatenate

`pd.merge(left, right, on="key", how="inner")` combines two DataFrames on a shared column,
similar to a SQL join. `how` can be `"inner"` (default, only matching keys), `"left"`, `"right"`,
or `"outer"` (union of keys, with NaN for non-matches). If the join column has different names
in each frame, use `left_on=` and `right_on=` instead of `on=`.

When both frames have other columns with the same name, pandas auto-suffixes them `_x` / `_y`;
control this with `suffixes=("_left", "_right")`.

`pd.concat([df1, df2])` stacks DataFrames (rows by default, `axis=0`); use `axis=1` to place them
side by side on a shared index. `pd.concat(..., ignore_index=True)` resets the index instead of
keeping the original (often-duplicated) row labels.

Common errors:
- A merge that silently produces far more rows than expected usually means the join key has
  duplicate values on one or both sides (a many-to-many join), causing a Cartesian product on
  those keys. Pass `validate="one_to_one"` / `"one_to_many"` / `"many_to_one"` to `merge()` to
  raise a `MergeError` early if your assumption about cardinality is wrong.
- `KeyError` on `on="key"` -- the column name doesn't exist in one of the two frames; verify with
  `"key" in left.columns and "key" in right.columns`.
- Merging on columns with mismatched dtypes (e.g. one side `int64` IDs, the other `object`/string
  IDs) silently returns zero matches rather than erroring. Cast both sides to the same dtype
  first, e.g. `left["id"].astype(str)`.
- After `pd.concat`, leftover duplicate index labels can cause confusing `.loc[]` lookups later;
  use `ignore_index=True` unless you specifically need to preserve original labels.
