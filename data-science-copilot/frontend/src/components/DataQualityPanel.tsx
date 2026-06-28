import type { DatasetProfile } from "@/lib/types";
import DataTable from "./DataTable";

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-xl border border-platinum-700 bg-white-500 p-4">
      <div className="text-2xl font-semibold text-black-500">{value}</div>
      <div className="text-xs font-medium uppercase tracking-wide text-charcoal-500">{label}</div>
    </div>
  );
}

export default function DataQualityPanel({ profile }: { profile: DatasetProfile }) {
  const rows = profile.columns.map((c) => ({
    Column: c.name,
    Dtype: c.dtype,
    Nulls: c.null_count,
    "Null %": c.null_pct,
    Unique: c.unique_count,
    Examples: c.sample_values.join(", "),
  }));

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-3 gap-3">
        <StatCard label="Rows" value={profile.shape.rows} />
        <StatCard label="Columns" value={profile.shape.columns} />
        <StatCard label="Duplicate rows" value={profile.duplicate_rows} />
      </div>
      <DataTable
        columns={["Column", "Dtype", "Nulls", "Null %", "Unique", "Examples"]}
        rows={rows}
      />
    </div>
  );
}
