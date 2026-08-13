"use client";

import { useState } from "react";
import { errorMessage } from "@/lib/errors";
import {
  buildWeeklySummary,
  exportClientsAndHistoryCsv,
  isPlusPlan,
  type WeeklySummary,
} from "@/lib/plus-reports";

export function PlusActions() {
  if (!isPlusPlan()) return null;
  return <PlusActionsBar />;
}

function PlusActionsBar() {
  const [summary, setSummary] = useState<WeeklySummary | null>(null);
  const [busy, setBusy] = useState<"summary" | "csv" | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function onSummary() {
    setError(null);
    setBusy("summary");
    try {
      setSummary(await buildWeeklySummary());
    } catch (err) {
      setError(errorMessage(err, "No se pudo armar el resumen"));
    } finally {
      setBusy(null);
    }
  }

  async function onExport() {
    setError(null);
    setBusy("csv");
    try {
      await exportClientsAndHistoryCsv();
    } catch (err) {
      setError(errorMessage(err, "No se pudo exportar"));
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="mb-5">
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          disabled={busy !== null}
          onClick={() => void onSummary()}
          className="tap-target rounded-md border border-line bg-surface px-4 py-2.5 text-sm font-semibold text-ink hover:bg-chip disabled:opacity-60"
        >
          {busy === "summary" ? "Armando…" : "Resumen semanal"}
        </button>
        <button
          type="button"
          disabled={busy !== null}
          onClick={() => void onExport()}
          className="tap-target rounded-md border border-line bg-surface px-4 py-2.5 text-sm font-semibold text-ink hover:bg-chip disabled:opacity-60"
        >
          {busy === "csv" ? "Exportando…" : "Exportar CSV"}
        </button>
      </div>
      {error && (
        <p role="alert" className="mt-2 text-sm text-red-700">
          {error}
        </p>
      )}

      {summary && (
        <div
          className="fixed inset-0 z-50 flex items-end justify-center bg-black/50 p-4 sm:items-center"
          role="dialog"
          aria-modal="true"
        >
          <div className="max-h-[90dvh] w-full max-w-md overflow-y-auto rounded-lg border border-line bg-surface p-5 shadow-xl">
            <h2 className="font-[family-name:var(--font-display)] text-lg font-bold text-ink">
              Resumen semanal
            </h2>
            <p className="mt-1 text-sm text-muted">
              {summary.workshop} · {summary.fromLabel} al {summary.toLabel}
            </p>
            <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
              <Stat label="Abiertas ahora" value={summary.openNow} />
              <Stat label="Esperando" value={summary.waiting} />
              <Stat label="Listos" value={summary.ready} />
              <Stat label="Altas esta semana" value={summary.createdThisWeek} />
              <Stat
                label="Entregados esta semana"
                value={summary.deliveredThisWeek}
              />
            </dl>
            {summary.byStatus.length > 0 && (
              <ul className="mt-4 space-y-1 text-sm text-ink">
                {summary.byStatus.map((s) => (
                  <li key={s.status}>
                    {s.label}: {s.count}
                  </li>
                ))}
              </ul>
            )}
            {summary.openTitles.length > 0 && (
              <div className="mt-4">
                <p className="text-xs font-semibold uppercase tracking-wide text-muted">
                  Abiertas
                </p>
                <ul className="mt-1 space-y-1 text-sm text-ink">
                  {summary.openTitles.map((t, i) => (
                    <li key={`${i}-${t}`}>· {t}</li>
                  ))}
                </ul>
              </div>
            )}
            <button
              type="button"
              onClick={() => setSummary(null)}
              className="btn-brand tap-target mt-5 w-full rounded-md px-4 py-2.5 text-sm font-semibold"
            >
              Cerrar
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-md border border-line px-3 py-2">
      <dt className="text-xs text-muted">{label}</dt>
      <dd className="font-[family-name:var(--font-display)] text-lg font-bold text-ink">
        {value}
      </dd>
    </div>
  );
}
