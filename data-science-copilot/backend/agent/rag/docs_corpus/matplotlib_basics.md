# Matplotlib: pyplot Basics for Generated Charts

The standard pattern for a script that must save (not interactively show) a chart:

```python
fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(x, y)            # or ax.bar(...), ax.scatter(...), ax.hist(...)
ax.set_title("Title")
ax.set_xlabel("X label")
ax.set_ylabel("Y label")
plt.tight_layout()
plt.savefig("chart.png", bbox_inches="tight", dpi=150)
```

Use the object-oriented `fig, ax = plt.subplots()` style rather than bare `plt.plot(...)` when
producing multiple charts in one script, to avoid plotting onto the wrong figure. Always call
`plt.close(fig)` (or `plt.close("all")`) after saving in a long-running process to free memory --
not required for a single one-shot script but good practice.

A pandas Series/DataFrame has a convenience `.plot()` method that wraps matplotlib:
`series.plot(kind="bar", ax=ax)`, `kind` can be `"bar"`, `"line"`, `"hist"`, `"box"`, `"pie"`,
`"scatter"` (needs `x=`, `y=`).

Common errors:
- `ax.bar(categories, values)` raises `TypeError`/`ValueError` if `values` contains NaN or
  non-numeric strings -- coerce/clean the numeric column first (`pd.to_numeric(errors="coerce")`,
  then `dropna()`).
- A blank/empty saved PNG usually means the DataFrame passed to plotting was empty after a filter
  -- check `len(df) > 0` before plotting and surface a clear message in `insights` if so.
- `RuntimeError: main thread is not in main loop` or backend errors only happen with interactive
  backends; in a headless sandboxed script, `matplotlib.use("Agg")` (already configured by this
  environment) avoids any GUI backend entirely.
- Overlapping x-axis labels on bar charts with many categories: rotate with
  `ax.tick_params(axis="x", rotation=45)` or `plt.setp(ax.get_xticklabels(), rotation=45,
  ha="right")`.
