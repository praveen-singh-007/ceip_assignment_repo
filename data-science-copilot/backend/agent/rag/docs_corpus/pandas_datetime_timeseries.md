# Pandas: Datetime and Time Series

Convert a column to real datetimes with `pd.to_datetime(df["col"], errors="coerce")`. Once a
column is `datetime64[ns]`, the `.dt` accessor exposes `.dt.year`, `.dt.month`, `.dt.day_name()`,
`.dt.to_period("M")`, etc.

For trend analysis ("is my traffic growing?"), the standard pattern: set the datetime column as
the index (`df = df.set_index("date")`), then resample to a coarser frequency and aggregate:
`df.resample("ME")["visits"].sum()` (month-end; use `"W"` for weekly, `"D"` for daily, `"QE"` for
quarterly). The result is a time-ordered Series ready to `.plot()` as a line chart.

A simple, explainable growth check: compare the first and last period in a resampled Series, or
fit a linear trend with `np.polyfit(range(len(series)), series.values, 1)` -- a positive slope
means growth, negative means decline. Percent change between consecutive periods:
`series.pct_change()`.

Common errors:
- `TypeError: Cannot compare tz-naive and tz-aware timestamps` -- one datetime column has
  timezone info and another doesn't; standardize with `.dt.tz_localize(None)` or
  `.dt.tz_convert(...)`.
- Resampling fails with `TypeError: Only valid with DatetimeIndex` -- the index isn't actually a
  `DatetimeIndex` yet; confirm with `df.index.dtype` and re-run `pd.to_datetime` /
  `set_index` first.
- Mixed date formats in one column (`"2024-01-05"` and `"01/05/2024"`) cause `to_datetime` to
  raise or silently mis-parse; consider `pd.to_datetime(col, errors="coerce", format="mixed")`.
- An all-NaT column after `to_datetime(errors="coerce")` usually means the source format didn't
  match at all -- inspect a few raw values before assuming the column is genuinely empty.
