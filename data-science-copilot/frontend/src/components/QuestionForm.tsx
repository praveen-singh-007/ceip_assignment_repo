import { ArrowUp, Loader2 } from "lucide-react";

interface QuestionFormProps {
  draft: string;
  onDraftChange: (value: string) => void;
  onSubmit: (question: string) => void;
  busy: boolean;
}

export default function QuestionForm({
  draft,
  onDraftChange,
  onSubmit,
  busy,
}: QuestionFormProps) {
  function submit() {
    if (draft.trim() && !busy) onSubmit(draft.trim());
  }

  return (
    <div className="flex items-end gap-2 rounded-2xl border border-platinum-700 bg-white-500 p-2 pl-4 transition-colors focus-within:border-charcoal-500">
      <textarea
        value={draft}
        onChange={(e) => onDraftChange(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            submit();
          }
        }}
        placeholder="Ask anything about this dataset…"
        rows={1}
        className="flex-1 resize-none bg-transparent py-2 text-sm text-black-500 placeholder:text-dim_grey-500 focus:outline-none"
      />
      <button
        onClick={submit}
        disabled={busy || !draft.trim()}
        className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-black-500 text-white-500 transition-colors hover:bg-graphite-500 disabled:cursor-not-allowed disabled:opacity-30"
      >
        {busy ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <ArrowUp className="h-4 w-4" />
        )}
      </button>
    </div>
  );
}
