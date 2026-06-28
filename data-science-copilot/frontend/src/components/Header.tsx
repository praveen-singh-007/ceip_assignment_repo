import type { HealthResponse } from "@/lib/types";

export default function Header({ health }: { health: HealthResponse | null }) {
  return (
    <header className="border-b border-platinum-700 bg-white-500">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-8 py-5">
        <span className="text-[15px] font-semibold tracking-tight text-black-500">
          Data Co-Pilot
        </span>
        <span className="text-xs text-charcoal-500">
          {health ? health.model : "Connecting…"}
        </span>
      </div>
    </header>
  );
}
