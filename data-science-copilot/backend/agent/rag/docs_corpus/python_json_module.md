# Python: json Module Gotchas

`json.dumps(obj)` only serializes plain Python types natively: `dict`, `list`, `str`, `int`,
`float`, `bool`, `None`. It raises `TypeError: Object of type X is not JSON serializable` for
anything else -- notably **pandas Timestamps, numpy integer/float types (`np.int64`,
`np.float64`), and `Decimal`** are all common offenders when serializing analysis results.

Fixes:
- Pass `default=str` to `json.dumps(obj, default=str)` to stringify any type it doesn't know
  natively -- the simplest catch-all fix for mixed pandas/numpy result objects.
- Convert numpy scalars back to native Python first: `int(np_int64_value)`,
  `float(np_float64_value)`.
- For a DataFrame/Series specifically, prefer `df.to_dict(orient="records")` (and `.astype(str)`
  on tricky columns first) over manually building a dict for JSON export.

`json.loads(text)` parses a JSON string into Python objects; raises
`json.JSONDecodeError` (a subclass of `ValueError`) on malformed JSON -- often caused by trailing
commas, single quotes instead of double quotes, or `NaN`/`Infinity` literals that aren't valid
strict JSON (Python's `json` module accepts these as an extension by default, but other JSON
parsers may not).
