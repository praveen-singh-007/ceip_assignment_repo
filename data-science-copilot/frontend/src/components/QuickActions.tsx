const QUICK_ACTIONS: { label: string; prompt: string }[] = [
  {
    label: "Sales dashboard",
    prompt:
      "Pick the most relevant numeric metric (e.g. revenue/sales) and the most relevant " +
      "categorical column (e.g. region/category/product) from this dataset's actual columns, " +
      "show the metric broken down by that category as a bar chart, and tell me which one leads.",
  },
  {
    label: "Data quality audit",
    prompt:
      "Run a full data quality audit: missing values, duplicate rows, and outliers in the " +
      "numeric columns, and summarize the findings.",
  },
  {
    label: "Trend analysis",
    prompt:
      "Is the main numeric metric in this dataset trending up or down over time? Plot the " +
      "trend and explain what you see.",
  },
  {
    label: "Cohort analysis",
    prompt:
      "Segment the records into cohorts based on the most relevant spend or activity column " +
      "and show a grouped chart comparing the cohorts.",
  },
];

export default function QuickActions({ onPick }: { onPick: (prompt: string) => void }) {
  return (
    <div className="flex flex-wrap gap-2">
      {QUICK_ACTIONS.map((action) => (
        <button
          key={action.label}
          onClick={() => onPick(action.prompt)}
          className="rounded-full border border-platinum-700 bg-white-500 px-3.5 py-1.5 text-xs font-medium text-charcoal-400 transition-colors hover:border-black-500 hover:text-black-500"
        >
          {action.label}
        </button>
      ))}
    </div>
  );
}
