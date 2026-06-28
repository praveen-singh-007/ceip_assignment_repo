# Python: Built-in Exception Reference

Quick reference for diagnosing tracebacks raised by generated analysis code:

- **KeyError** -- a dict key / DataFrame column / Series label doesn't exist. In pandas, almost
  always means a column name typo, leading/trailing whitespace, or wrong case.
- **ValueError** -- a value has the right *type* but an inappropriate *value* for the operation,
  e.g. `astype(float)` on the string `"abc"`, or `pd.to_datetime` on an unparseable date string,
  or unpacking the wrong number of items (`a, b = [1, 2, 3]`).
- **TypeError** -- an operation got a value of the wrong *type* entirely, e.g. adding a string to
  an int, calling a method that doesn't exist on that type, or `.str` accessor on a numeric
  column.
- **IndexError** -- a sequence/array index is out of range (`lst[10]` when `len(lst) == 3`, or
  `.iloc[100]` on a 50-row DataFrame).
- **AttributeError** -- accessing a method/attribute that doesn't exist on that object, e.g.
  calling `.str` on a `datetime64` column, or a typo'd pandas method name.
- **ZeroDivisionError** -- raised by plain Python division `x / 0`; note NumPy/pandas float
  division by zero does NOT raise this, it silently returns `inf`/`nan` with a `RuntimeWarning`.
- **ImportError / ModuleNotFoundError** -- the code tried to `import` something not available in
  the sandboxed environment (only pandas, numpy, matplotlib, seaborn, json, math, re, statistics,
  datetime, collections, itertools are permitted here); remove the import and use only the
  allowed libraries.

When fixing code based on a traceback, always read the **last** line for the exception type and
message, and the line immediately above the traceback's final frame for the exact line of user
code that triggered it -- intermediate frames are usually internal pandas/numpy implementation
detail and not where the actual fix belongs.
