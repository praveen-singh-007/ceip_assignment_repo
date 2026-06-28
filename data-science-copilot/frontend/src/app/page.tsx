"use client";

import { useEffect, useState } from "react";
import Header from "@/components/Header";
import DatasetPicker from "@/components/DatasetPicker";
import DatasetSummaryBar from "@/components/DatasetSummaryBar";
import SegmentedControl from "@/components/SegmentedControl";
import DataTable from "@/components/DataTable";
import DataQualityPanel from "@/components/DataQualityPanel";
import QuickActions from "@/components/QuickActions";
import QuestionForm from "@/components/QuestionForm";
import AnalysisResultCard from "@/components/AnalysisResultCard";
import Spinner from "@/components/Spinner";
import { askQuestion, getHealth, listSamples } from "@/lib/api";
import type {
  AskResponse,
  DatasetLoadResponse,
  HealthResponse,
  SampleDatasetInfo,
} from "@/lib/types";

type Tab = "preview" | "quality" | "ask";

const TAB_OPTIONS: { value: Tab; label: string }[] = [
  { value: "preview", label: "Preview" },
  { value: "quality", label: "Data quality" },
  { value: "ask", label: "Ask" },
];

export default function Home() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [samples, setSamples] = useState<SampleDatasetInfo[]>([]);
  const [dataset, setDataset] = useState<DatasetLoadResponse | null>(null);
  const [tab, setTab] = useState<Tab>("preview");
  const [draft, setDraft] = useState("");
  const [history, setHistory] = useState<AskResponse[]>([]);
  const [busy, setBusy] = useState(false);
  const [askError, setAskError] = useState<string | null>(null);

  useEffect(() => {
    getHealth().then(setHealth).catch(() => setHealth(null));
    listSamples().then(setSamples).catch(() => setSamples([]));
  }, []);

  function handleDatasetLoaded(loaded: DatasetLoadResponse) {
    setDataset(loaded);
    setHistory([]);
    setAskError(null);
    setTab("preview");
  }

  async function handleAsk(question: string) {
    if (!dataset) return;
    setBusy(true);
    setAskError(null);
    try {
      const result = await askQuestion(dataset.session_id, question);
      setHistory((prev) => [result, ...prev]);
      setDraft("");
    } catch (err) {
      setAskError(err instanceof Error ? err.message : "Could not reach the backend.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-screen flex-col">
      <Header health={health} />
      <main className="flex-1">
        {!dataset ? (
          <DatasetPicker samples={samples} onLoaded={handleDatasetLoaded} />
        ) : (
          <div className="mx-auto max-w-7xl space-y-8 px-8 py-10">
            <DatasetSummaryBar dataset={dataset} onChangeDataset={() => setDataset(null)} />

            <SegmentedControl value={tab} options={TAB_OPTIONS} onChange={setTab} />

            {tab === "preview" && <DataTable columns={dataset.columns} rows={dataset.preview} />}

            {tab === "quality" && <DataQualityPanel profile={dataset.profile} />}

            {tab === "ask" && (
              <div className="space-y-6">
                <QuickActions onPick={setDraft} />
                <QuestionForm
                  draft={draft}
                  onDraftChange={setDraft}
                  onSubmit={handleAsk}
                  busy={busy}
                />
                {busy && (
                  <Spinner label="Writing and running code, self-correcting on errors…" />
                )}
                {askError && (
                  <p className="rounded-xl border border-platinum-700 bg-white-500 px-4 py-3 text-sm text-charcoal-300">
                    {askError}
                  </p>
                )}
                <div className="space-y-4">
                  {history.map((item, i) => (
                    <AnalysisResultCard key={i} result={item} />
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
