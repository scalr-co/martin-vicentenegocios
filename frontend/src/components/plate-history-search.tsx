"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { fieldClass } from "@/lib/form-styles";

export function PlateHistorySearch({
  initialPlate = "",
  compact = false,
}: {
  initialPlate?: string;
  compact?: boolean;
}) {
  const router = useRouter();
  const [plate, setPlate] = useState(initialPlate);

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    const q = plate.trim();
    if (!q) return;
    router.push(`/panel/historial?plate=${encodeURIComponent(q)}`);
  }

  return (
    <form
      onSubmit={onSubmit}
      className={
        compact
          ? "mb-5 flex flex-col gap-2 sm:flex-row sm:items-end"
          : "flex flex-col gap-2 sm:flex-row sm:items-end"
      }
    >
      <label className="block min-w-0 flex-1" htmlFor="history-plate">
        <span className="text-xs font-semibold uppercase tracking-wide text-muted">
          Historial por patente
        </span>
        <input
          id="history-plate"
          value={plate}
          onChange={(e) => setPlate(e.target.value.toUpperCase())}
          className={`${fieldClass} uppercase`}
          placeholder="ABCD12"
          autoComplete="off"
          spellCheck={false}
        />
      </label>
      <button
        type="submit"
        className="btn-brand tap-target inline-flex items-center justify-center rounded-md px-4 py-2.5 text-sm font-semibold"
      >
        Ver historial
      </button>
    </form>
  );
}
