# Seaborn: Statistical Plotting Basics

Seaborn (`import seaborn as sns`) works on top of matplotlib and is built around "tidy"
(long-form) DataFrames: one row per observation, with categorical/grouping variables as their own
columns. Pass the DataFrame directly via `data=df` and reference column names as strings for
`x=`, `y=`, and `hue=` (the grouping/color-split variable) -- you generally do not need to
pre-aggregate before calling seaborn functions like `sns.barplot`, which aggregates (mean, by
default) automatically.

Common functions: `sns.barplot(data=df, x="region", y="revenue")` (categorical bar with
confidence interval), `sns.lineplot(data=df, x="date", y="value", hue="category")`,
`sns.boxplot`/`sns.violinplot` (distribution by category, good for outlier visualization),
`sns.heatmap(corr_matrix, annot=True, cmap="coolwarm")` (correlation heatmaps -- pass
`df.corr(numeric_only=True)`), `sns.pairplot(df)` (pairwise scatter grid, only use on a handful
of columns -- it is O(n^2) in column count and slow on wide DataFrames).

To draw into a specific matplotlib `Axes` (so titles/labels/savefig still work the normal
matplotlib way), pass `ax=ax`: `sns.barplot(data=df, x="region", y="revenue", ax=ax)`.

Common errors:
- `sns.barplot`/`lineplot` raising on a wide (pivoted) DataFrame -- seaborn expects long-form
  data; use `df.melt(id_vars=..., var_name=..., value_name=...)` to reshape wide data to long
  first.
- `ValueError: could not convert string to float` inside a seaborn numeric plot -- same root
  cause as matplotlib: a "numeric" column is still `object` dtype with stray text; clean with
  `pd.to_numeric(errors="coerce")` before plotting.
- `sns.heatmap` on a DataFrame that still has non-numeric columns -- restrict to
  `df.select_dtypes(include="number")` before calling `.corr()`.
