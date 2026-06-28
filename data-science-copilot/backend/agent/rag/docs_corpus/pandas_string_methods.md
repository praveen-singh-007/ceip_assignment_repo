# Pandas: String (.str) Methods

Object/string columns expose vectorized string operations through the `.str` accessor, mirroring
Python's built-in `str` methods but NaN-safe (they propagate NaN instead of raising):
`df["col"].str.strip()`, `.str.lower()`, `.str.contains("pattern", case=False, na=False)`,
`.str.replace(old, new, regex=False)`, `.str.split(",")`, `.str.extract(r"(\d+)")` (regex capture
groups, returns a DataFrame of matches).

Always pass `na=False` to `.str.contains()` when filtering rows (`df[df["col"].str.contains(...)]`)
-- otherwise rows where `col` is NaN produce `NaN` in the mask, and boolean-indexing with NaN in
the mask raises.

Common errors:
- `AttributeError: Can only use .str accessor with string values` -- the column's dtype isn't
  actually string/object (e.g. it's numeric or already datetime); cast with `.astype(str)` first
  if you genuinely need string ops on it.
- Calling `.str.replace(old, new)` expecting regex by default -- since pandas 1.0+ behavior
  depends on the `regex=` argument; pass `regex=True` explicitly if `old` is a regex pattern, or
  `regex=False` for a literal substring replace, to avoid ambiguous warnings/errors with special
  regex characters like `.` or `(`.
- `.str.split(",", expand=True)` returns a DataFrame (one column per split part) instead of a
  Series of lists -- useful for splitting a "First Last" name column into two columns directly.
