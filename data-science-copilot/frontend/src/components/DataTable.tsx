interface DataTableProps {
  columns: string[];
  rows: Record<string, unknown>[];
  maxRows?: number;
}

export default function DataTable({ columns, rows, maxRows }: DataTableProps) {
  const displayRows = maxRows ? rows.slice(0, maxRows) : rows;

  if (displayRows.length === 0) {
    return <p className="text-sm text-charcoal-500">No rows to display.</p>;
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-platinum-700 bg-white-500">
      <table className="min-w-full text-left text-sm">
        <thead className="border-b border-platinum-700">
          <tr>
            {columns.map((col) => (
              <th
                key={col}
                className="whitespace-nowrap px-4 py-2.5 text-xs font-semibold uppercase tracking-wide text-charcoal-500"
              >
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-alabaster_grey-700">
          {displayRows.map((row, i) => (
            <tr key={i} className="transition-colors hover:bg-alabaster_grey-900">
              {columns.map((col) => (
                <td key={col} className="whitespace-nowrap px-4 py-2.5 text-charcoal-200">
                  {String(row[col] ?? "")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
