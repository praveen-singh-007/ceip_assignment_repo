# Pandas: Dtypes and Type Conversion

Every column (`Series`) has a `dtype`: common ones are `int64`, `float64`, `object` (usually
strings or mixed types), `bool`, `datetime64[ns]`, and `category`. Inspect with `df.dtypes` or
`df["col"].dtype`.

`df["col"].astype(new_type)` casts a column, but **raises `ValueError` or `TypeError` if any
value cannot be converted** -- e.g. `astype(float)` on a column containing `"N/A"` strings fails
hard. For real-world messy data, prefer the coercing converters:

- `pd.to_numeric(df["col"], errors="coerce")` converts to numeric and turns anything
  unparseable into `NaN` instead of raising.
- `pd.to_datetime(df["col"], errors="coerce")` does the same for dates; combine with `format=`
  when you know the exact format (much faster and avoids ambiguous parsing like
  day-first vs month-first).
- `df["col"].astype(str)` almost never raises since nearly anything can be stringified, but
  note it will turn actual `NaN` into the *string* `"nan"` -- fillna first if you don't want that.

Common errors:
- `ValueError: could not convert string to float: 'xyz'` -- a column you assumed was numeric has
  stray text (e.g. `"N/A"`, `"-"`, currency symbols, thousands separators like `"1,200"`). Strip
  symbols/commas with `.str.replace(",", "")` then use `pd.to_numeric(..., errors="coerce")`.
- `TypeError: Invalid comparison between dtype=datetime64[ns] and str` -- compare datetimes to
  `pd.Timestamp(...)` or another datetime, not a raw string.
- Mixing `int` columns containing NaN: pandas silently upcasts the whole column to `float64`
  because NaN has no integer representation. Use the nullable `Int64` (capital I) dtype via
  `astype("Int64")` if you need integers with missing values.
- Category dtype (`astype("category")`) is useful for low-cardinality string columns (e.g.
  region, status) -- it speeds up `groupby` and reduces memory.
