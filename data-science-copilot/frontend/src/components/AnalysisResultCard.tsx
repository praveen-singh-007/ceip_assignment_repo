"use client";

import { useState } from "react";
import { Check, ChevronDown, Download, X } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Components } from "react-markdown";
import type { AskResponse } from "@/lib/types";
import { resolveFileUrl } from "@/lib/api";
import DataTable from "./DataTable";

const reportComponents: Components = {
  h1: ({ children }) => (
    <h1 className="mb-2 mt-6 text-base font-semibold text-black-500 first:mt-0">{children}</h1>
  ),
  h2: ({ children }) => (
    <h2 className="mb-2 mt-6 text-xs font-semibold uppercase tracking-wide text-charcoal-500">
      {children}
    </h2>
  ),
  p: ({ children }) => (
    <p className="mb-3 text-sm leading-relaxed text-charcoal-300">{children}</p>
  ),
  strong: ({ children }) => <strong className="font-semibold text-black-500">{children}</strong>,
  ul: ({ children }) => (
    <ul className="mb-3 list-disc space-y-1 pl-5 text-sm text-charcoal-300">{children}</ul>
  ),
  li: ({ children }) => <li>{children}</li>,
  hr: () => <hr className="my-4 border-alabaster_grey-700" />,
  img: ({ src, alt }) => (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={typeof src === "string" ? src : undefined}
      alt={alt ?? ""}
      className="mb-3 w-full rounded-xl border border-alabaster_grey-700"
    />
  ),
  table: ({ children }) => (
    <div className="mb-3 overflow-x-auto rounded-lg border border-alabaster_grey-700">
      <table className="min-w-full text-left text-sm">{children}</table>
    </div>
  ),
  thead: ({ children }) => <thead className="border-b border-platinum-700">{children}</thead>,
  th: ({ children }) => (
    <th className="whitespace-nowrap px-3 py-2 text-xs font-semibold uppercase tracking-wide text-charcoal-500">
      {children}
    </th>
  ),
  td: ({ children }) => (
    <td className="whitespace-nowrap border-t border-alabaster_grey-700 px-3 py-2 text-charcoal-200">
      {children}
    </td>
  ),
  pre: ({ children }) => (
    <pre className="mb-3 overflow-x-auto rounded-lg bg-carbon_black-500 p-3 text-xs text-platinum-600 [&_code]:bg-transparent [&_code]:p-0 [&_code]:text-platinum-600">
      {children}
    </pre>
  ),
  code: ({ children }) => (
    <code className="rounded bg-alabaster_grey-800 px-1 py-0.5 font-mono text-[0.85em] text-charcoal-200">
      {children}
    </code>
  ),
};

export default function AnalysisResultCard({ result }: { result: AskResponse }) {
  const [showTrace, setShowTrace] = useState(false);
  const [showReport, setShowReport] = useState(false);
  const [reportMarkdown, setReportMarkdown] = useState<string | null>(null);
  const [reportLoading, setReportLoading] = useState(false);

  async function toggleReportPreview() {
    if (showReport) {
      setShowReport(false);
      return;
    }
    setShowReport(true);
    if (reportMarkdown || !result.report_url) return;
    setReportLoading(true);
    try {
      const res = await fetch(resolveFileUrl(result.report_url) ?? "");
      setReportMarkdown(await res.text());
    } catch {
      setReportMarkdown("Could not load the report preview.");
    } finally {
      setReportLoading(false);
    }
  }

  const resultRows =
    result.result?.type === "dataframe" && Array.isArray(result.result.data)
      ? (result.result.data as Record<string, unknown>[])
      : null;

  return (
    <div className="rounded-2xl border border-platinum-700 bg-white-500 p-6">
      <div className="flex items-start justify-between gap-4 border-b border-alabaster_grey-700 pb-4">
        <p className="max-w-3xl text-[15px] font-medium leading-snug text-black-500">
          {result.question}
        </p>
        <span
          className={`flex shrink-0 items-center gap-1 text-xs font-medium ${
            result.success ? "text-charcoal-400" : "text-charcoal-500"
          }`}
        >
          {result.success ? <Check className="h-3.5 w-3.5" /> : <X className="h-3.5 w-3.5" />}
          {result.success ? "Completed" : "Failed"}
        </span>
      </div>

      <div className="space-y-5 pt-5">
        {result.success ? (
          <>
            {result.chart_urls.length > 0 && (
              <div
                className={`grid gap-3 ${result.chart_urls.length > 1 ? "sm:grid-cols-2" : ""}`}
              >
                {result.chart_urls.map((url) => (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    key={url}
                    src={resolveFileUrl(url) ?? undefined}
                    alt="Generated chart"
                    className="w-full rounded-xl border border-alabaster_grey-700"
                  />
                ))}
              </div>
            )}
            {result.insights && (
              <p className="max-w-3xl border-l-2 border-black-500 pl-4 text-sm leading-relaxed text-charcoal-300">
                {result.insights}
              </p>
            )}
            {resultRows && (
              <DataTable
                columns={result.result?.columns ?? Object.keys(resultRows[0] ?? {})}
                rows={resultRows}
              />
            )}
          </>
        ) : (
          <p className="whitespace-pre-wrap rounded-xl border border-alabaster_grey-700 bg-alabaster_grey-900 px-4 py-3 text-xs text-charcoal-300">
            {result.attempts.at(-1)?.error?.slice(-1500) ?? "Unknown error."}
          </p>
        )}

        <div className="flex flex-wrap items-center gap-4 text-xs">
          {result.report_url && (
            <>
              <a
                href={resolveFileUrl(result.report_url) ?? undefined}
                download
                className="flex items-center gap-1.5 font-medium text-charcoal-400 transition-colors hover:text-black-500"
              >
                <Download className="h-3.5 w-3.5" />
                Download report
              </a>
              <button
                onClick={toggleReportPreview}
                className="flex items-center gap-1 font-medium text-charcoal-400 transition-colors hover:text-black-500"
              >
                <ChevronDown
                  className={`h-3.5 w-3.5 transition-transform ${showReport ? "rotate-180" : ""}`}
                />
                Preview report
              </button>
            </>
          )}
          <button
            onClick={() => setShowTrace((v) => !v)}
            className="flex items-center gap-1 font-medium text-charcoal-400 transition-colors hover:text-black-500"
          >
            <ChevronDown
              className={`h-3.5 w-3.5 transition-transform ${showTrace ? "rotate-180" : ""}`}
            />
            {result.attempts.length > 1 ? `${result.attempts.length} attempts` : "View code"}
          </button>
        </div>

        {showReport && (
          <div className="max-h-[32rem] overflow-auto rounded-xl border border-alabaster_grey-700 bg-white-500 p-5">
            {reportLoading ? (
              <p className="text-xs text-charcoal-400">Loading…</p>
            ) : (
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={reportComponents}
                urlTransform={(url) => url}
              >
                {reportMarkdown}
              </ReactMarkdown>
            )}
          </div>
        )}

        {showTrace && (
          <div className="space-y-3">
            {result.attempts.map((a) => (
              <div
                key={a.attempt_number}
                className="rounded-xl border border-alabaster_grey-700 p-4"
              >
                <p className="flex items-center gap-1.5 text-xs font-medium text-black-500">
                  {a.success ? <Check className="h-3 w-3" /> : <X className="h-3 w-3" />}
                  Attempt {a.attempt_number}
                </p>
                <pre className="mt-2 overflow-x-auto rounded-lg bg-carbon_black-500 p-3 text-xs text-platinum-600">
                  {a.code}
                </pre>
                {a.error && (
                  <p className="mt-2 text-xs text-charcoal-400">{a.error.slice(-800)}</p>
                )}
                {a.retrieved_doc_sources.length > 0 && (
                  <p className="mt-2 text-xs text-charcoal-500">
                    Reference docs: {a.retrieved_doc_sources.join(", ")}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
