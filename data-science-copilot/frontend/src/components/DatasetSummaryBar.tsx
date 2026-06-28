import { ArrowLeft } from "lucide-react";
import type { DatasetLoadResponse } from "@/lib/types";

interface DatasetSummaryBarProps {
  dataset: DatasetLoadResponse;
  onChangeDataset: () => void;
}

export default function DatasetSummaryBar({
  dataset,
  onChangeDataset,
}: DatasetSummaryBarProps) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-platinum-700 bg-white-500 px-5 py-4">
      <div>
        <p className="text-sm font-medium text-black-500">{dataset.dataset_name}</p>
        <p className="text-xs text-charcoal-500">
          {dataset.profile.shape.rows} rows · {dataset.profile.shape.columns} columns
          {dataset.profile.duplicate_rows > 0 &&
            ` · ${dataset.profile.duplicate_rows} duplicate rows`}
        </p>
      </div>
      <button
        onClick={onChangeDataset}
        className="flex items-center gap-1.5 text-xs font-medium text-charcoal-500 transition-colors hover:text-black-500"
      >
        <ArrowLeft className="h-3.5 w-3.5" />
        Change dataset
      </button>
    </div>
  );
}
