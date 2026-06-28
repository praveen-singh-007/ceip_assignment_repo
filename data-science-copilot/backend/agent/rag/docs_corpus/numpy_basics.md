# NumPy: Arrays, NaN, and Broadcasting

NumPy arrays (`np.array`, and the values underlying every pandas column) are homogeneously typed
and support vectorized elementwise operations (`a + b`, `a * 2`) without explicit loops, plus
broadcasting: operations between a `(n,)` array and a scalar, or an `(n, m)` array and a `(m,)`
array, apply automatically across the larger shape.

`np.nan` is a float and behaves like pandas' missing-value float: `np.nan == np.nan` is `False`;
use `np.isnan(x)` to test for it. Aggregations like `np.mean(arr)` propagate NaN by default
(result is NaN if any element is NaN) -- use `np.nanmean`, `np.nansum`, `np.nanstd`, etc. to skip
NaNs explicitly.

`np.where(condition, a, b)` is a vectorized ternary, very useful for creating a new column based
on a condition: `df["flag"] = np.where(df["value"] > 100, "high", "low")`.

Common errors:
- `ValueError: operands could not be broadcast together with shapes (...)` -- the two arrays'
  shapes are incompatible for broadcasting; check `.shape` on both sides, the trailing
  dimensions must match or be `1`.
- `RuntimeWarning: invalid value encountered in ...` -- usually from `0/0`, `log(negative)`, or
  similar; the result is `nan`/`inf` rather than a raised exception. Mask or filter inputs before
  the operation if this is unintended.
- Mixing Python lists and arrays inside `np.array([...])` with ragged (unequal) lengths raises
  `ValueError: setting an array element with a sequence` on recent NumPy versions, or produces an
  awkward `dtype=object` array -- ensure sub-lists are the same length before building a 2D array.
