"use client";

import { useState } from "react";
import { Loader2, Upload } from "lucide-react";
import type { DatasetLoadResponse, SampleDatasetInfo } from "@/lib/types";
import { loadSample, uploadDataset } from "@/lib/api";

interface DatasetPickerProps {
  samples: SampleDatasetInfo[];
  onLoaded: (dataset: DatasetLoadResponse) => void;
}

export default function DatasetPicker({ samples, onLoaded }: DatasetPickerProps) {
  const [loadingKey, setLoadingKey] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);

  async function handleSampleClick(key: string) {
    setError(null);
    setLoadingKey(key);
    try {
      onLoaded(await loadSample(key));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load that dataset.");
    } finally {
      setLoadingKey(null);
    }
  }

  async function handleFile(file: File) {
    setError(null);
    setLoadingKey("__upload__");
    try {
      onLoaded(await uploadDataset(file));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not read that file.");
    } finally {
      setLoadingKey(null);
    }
  }

  return (
    <div className="mx-auto max-w-4xl px-8 py-20">
      <div className="text-center">
        <h1 className="text-3xl font-semibold tracking-tight text-black-500">
          Turn raw data into answers
        </h1>
        <p className="mt-2 text-sm text-charcoal-500">
          Choose a sample dataset or upload your own CSV, Excel, or JSON file.
        </p>
      </div>

      {error && (
        <p className="mt-6 rounded-xl border border-platinum-700 bg-white-500 px-4 py-3 text-sm text-charcoal-400">
          {error}
        </p>
      )}

      <div className="mt-10 grid gap-3 sm:grid-cols-2">
        {samples.map((sample) => (
          <button
            key={sample.key}
            onClick={() => handleSampleClick(sample.key)}
            disabled={loadingKey !== null}
            className="flex flex-col gap-2 rounded-xl border border-platinum-700 bg-white-500 p-4 text-left transition-colors hover:border-charcoal-500 disabled:opacity-50"
          >
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-black-500">{sample.label}</span>
              <span className="rounded-full bg-alabaster_grey-800 px-2 py-0.5 text-[11px] font-medium uppercase tracking-wide text-charcoal-500">
                {sample.format}
              </span>
            </div>
            <p className="text-xs text-charcoal-400">{sample.description}</p>
            {loadingKey === sample.key && (
              <span className="flex items-center gap-1.5 text-xs text-charcoal-500">
                <Loader2 className="h-3 w-3 animate-spin" />
                Loading
              </span>
            )}
          </button>
        ))}

        {samples.length === 0 && (
          <p className="col-span-2 text-center text-xs text-charcoal-500">
            Loading sample datasets…
          </p>
        )}

        <label
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragOver(false);
            const file = e.dataTransfer.files?.[0];
            if (file) handleFile(file);
          }}
          className={`flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border border-dashed p-6 text-center transition-colors sm:col-span-2 ${
            dragOver
              ? "border-black-500 bg-alabaster_grey-800"
              : "border-platinum-700 bg-white-500 hover:border-charcoal-500"
          }`}
        >
          <Upload className="h-5 w-5 text-charcoal-500" />
          <span className="text-sm font-medium text-black-500">Upload your own file</span>
          <span className="text-xs text-charcoal-500">
            CSV, XLSX, or JSON — click or drag and drop
          </span>
          <input
            type="file"
            accept=".csv,.xlsx,.xls,.json"
            className="hidden"
            disabled={loadingKey !== null}
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) handleFile(file);
              e.target.value = "";
            }}
          />
          {loadingKey === "__upload__" && (
            <span className="flex items-center gap-1.5 text-xs text-charcoal-500">
              <Loader2 className="h-3 w-3 animate-spin" />
              Reading file
            </span>
          )}
        </label>
      </div>
    </div>
  );
}
