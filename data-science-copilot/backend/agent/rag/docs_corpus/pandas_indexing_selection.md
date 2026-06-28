# Pandas: Indexing and Selection

Use `df["col"]` or `df.col` to select a single column as a `Series`; `df[["a", "b"]]` (note the
double brackets) selects multiple columns and returns a `DataFrame`. `df.loc[row_label, col_label]`
selects by label, `df.iloc[row_pos, col_pos]` selects by integer position. Mixing them up is a
frequent source of bugs: `df.loc[0]` means "row with index label 0" (which may not be the first
row after filtering/sorting), while `df.iloc[0]` always means "the first row physically".

Boolean (mask) indexing: `df[df["col"] > 10]` filters rows. Combine conditions with `&` / `|`
(not Python's `and`/`or`) and wrap each condition in parentheses:
`df[(df["a"] > 10) & (df["b"] == "x")]`.

Common errors:
- `KeyError: 'col_name'` -- the column doesn't exist, often due to whitespace
  (`" Revenue"` vs `"Revenue"`), case mismatch, or a typo. Defensive code should check
  `"col_name" in df.columns` before accessing it, and/or strip column names with
  `df.columns = df.columns.str.strip()` right after loading.
- `KeyError` on `.loc[]` -- the label you asked for isn't in the index. Use `.get()` semantics
  via `df.loc[df.index.intersection([label])]` or check membership first.
- `SettingWithCopyWarning` -- you assigned into a slice that pandas isn't sure is a view or a
  copy. Use `df.loc[mask, "col"] = value` (a single `.loc` call) instead of chained indexing
  like `df[mask]["col"] = value`.
- `IndexError: single positional indexer is out-of-bounds` -- `.iloc[n]` where `n >= len(df)`;
  guard with `if len(df) > n`.
