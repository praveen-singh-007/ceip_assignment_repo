# Pandas: Reading CSV, Excel, and JSON

`pd.read_csv(path)` -- key parameters: `sep`/`delimiter` (defaults to `,`), `encoding` (try
`"utf-8"` first, then `"latin1"`/`"cp1252"` for files with special characters that fail to
decode), `parse_dates=["col"]` to parse specific columns as datetimes on load, `dtype={"col":
str}` to force a column's type (e.g. keep zip codes or IDs as strings instead of guessing int),
and `na_values=["NA", "N/A", "-"]` to treat extra tokens as missing.

`pd.read_excel(path, sheet_name=0)` reads Excel files (requires `openpyxl` for `.xlsx`, already
available). `sheet_name` can be an index (0-based), a sheet name string, or `None` to read every
sheet into a dict of DataFrames keyed by sheet name. `header=N` controls which row holds the
column names if the sheet has title rows above the real header.

`pd.read_json(path_or_buf, orient="records")` -- `orient="records"` expects a JSON array of
objects (most common export shape: `[{"a": 1}, {"b": 2}]`). If the JSON is instead a dict of
columns (`{"a": [1, 2], "b": [3, 4]}`), use `orient="columns"` (the default). For deeply nested
JSON, flatten first with `pd.json_normalize(data)` before building a DataFrame.

Common errors:
- `UnicodeDecodeError` on `read_csv` -- wrong `encoding` guess; retry with `encoding="latin1"`.
- `ParserError: Error tokenizing data` -- inconsistent column counts per row, often from
  unescaped commas inside a field; try `sep=None, engine="python"` to auto-detect, or
  `on_bad_lines="skip"` to drop malformed rows.
- `read_excel` raising about a missing engine -- `.xlsx` needs `openpyxl`, legacy `.xls` needs
  `xlrd`; this project's environment ships `openpyxl`.
- A whole numeric column read in as `object` dtype -- usually one stray non-numeric cell (e.g. a
  footer/total row, or a thousands separator like `"1,234"`); inspect with
  `df["col"].apply(type).value_counts()` then clean with `pd.to_numeric(errors="coerce")`.
