"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState, useSyncExternalStore } from "react";
import { AuthGuard } from "@/components/auth-guard";
import { PanelShell } from "@/components/panel-shell";
import { PlusActions } from "@/components/plus-actions";
import { PlateHistorySearch } from "@/components/plate-history-search";
import { StatusBadge } from "@/components/ui";
import { apiList } from "@/lib/api";
import { formatDateCl } from "@/lib/date";
import { errorMessage } from "@/lib/errors";
import { getStatuses, subscribeStatuses } from "@/lib/statuses";
import { formatVehicleOrItem, type ApiOrder } from "@/lib/types";

const FILTERS: { id: "open" | "critical" | string; label: string }[] = [
  { id: "open", label: "Abiertas" },
  { id: "critical", label: "Esperando" },
  { id: "en_reparacion", label: "En reparación" },
  { id: "listo", label: "Listos" },
];

function normalizeOrder(order: ApiOrder): ApiOrder {
  return {
    ...order,
    vehicleOrItem:
      order.vehicleOrItem ||
      formatVehicleOrItem(order.vehicle ?? null, "Sin vehículo"),
  };
}

export default function PanelPage() {
  return (
    <AuthGuard>
      <PanelContent />
    </AuthGuard>
  );
}

function PanelContent() {
  const [filter, setFilter] = useState<(typeof FILTERS)[number]["id"]>("open");
  const [orders, setOrders] = useState<ApiOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const statuses = useSyncExternalStore(
    subscribeStatuses,
    getStatuses,
    getStatuses,
  );

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const list = await apiList<ApiOrder>("/orders?open=true&limit=50");
      setOrders(list.map(normalizeOrder));
      setError(null);
    } catch (err) {
      setError(errorMessage(err, "No se pudieron cargar las órdenes"));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    function onOnline() {
      void load();
    }
    window.addEventListener("online", onOnline);
    return () => window.removeEventListener("online", onOnline);
  }, [load]);

  const waiting = orders.filter(
    (o) =>
      o.status === "esperando_aprobacion" || o.status === "esperando_repuesto",
  );
  const ready = orders.filter((o) => o.status === "listo");
  const statsReady = !loading && !error;

  const visible = useMemo(() => {
    if (filter === "open") return orders;
    if (filter === "critical") return waiting;
    return orders.filter((o) => o.status === filter);
  }, [filter, orders, waiting]);

  return (
    <PanelShell
      title="Órdenes de hoy"
      subtitle="Trabajos abiertos del taller"
    >
      <div className="mb-4 grid grid-cols-3 gap-2 sm:mb-6 sm:gap-3">
        <Stat
          label="Abiertas"
          value={statsReady ? orders.length : null}
          compact
        />
        <Stat
          label="Esperando"
          value={statsReady ? waiting.length : null}
          tone="warn"
          compact
        />
        <Stat
          label="Listos"
          value={statsReady ? ready.length : null}
          tone="ok"
          compact
        />
      </div>

      <PlusActions />

      <PlateHistorySearch compact />

      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap gap-2">
          {FILTERS.map((f) => (
            <button
              key={f.id}
              type="button"
              onClick={() => setFilter(f.id)}
              className={`tap-target rounded-full px-3 py-1.5 text-xs font-medium transition ${
                filter === f.id
                  ? "bg-brand text-brand-ink"
                  : "bg-surface text-muted ring-1 ring-line hover:text-ink"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
        <Link
          href="/panel/nueva-orden"
          className="btn-brand hidden rounded-md px-4 py-2 text-sm font-semibold sm:inline-flex"
        >
          Nueva orden
        </Link>
      </div>

      {loading && <p className="text-sm text-muted">Cargando órdenes…</p>}
      {error && (
        <div
          role="alert"
          className="rounded-md border border-red-200 bg-danger-soft px-3 py-3 text-sm text-red-800 dark:text-red-200"
        >
          <p>{error}</p>
          <button
            type="button"
            onClick={() => void load()}
            className="tap-target mt-2 rounded-md border border-red-300 bg-surface px-3 py-1.5 text-sm font-semibold text-red-800 dark:text-red-200"
          >
            Reintentar
          </button>
        </div>
      )}

      {!loading && !error && (
        <ul className="space-y-3 pb-28 sm:pb-0">
          {visible.map((order) => (
            <li key={order.id}>
              <Link
                href={`/panel/ordenes/${order.id}`}
                className="card-lift block min-w-0 rounded-lg border border-line bg-surface p-4 hover:border-stone-300"
              >
                <div className="flex min-w-0 items-start justify-between gap-2">
                  <div className="min-w-0 flex-1 overflow-hidden">
                    <p className="font-semibold text-ink">{order.title}</p>
                    <p className="mt-0.5 truncate text-sm text-muted">
                      {order.client?.name ?? "Cliente"} ·{" "}
                      {order.vehicleOrItem}
                    </p>
                  </div>
                  <StatusBadge status={order.status} />
                </div>
                {order.estimatedAt && (
                  <p className="mt-3 text-xs text-muted">
                    Estimado: {formatDateCl(order.estimatedAt)}
                  </p>
                )}
              </Link>
            </li>
          ))}
          {visible.length === 0 && (
            <li className="rounded-lg border border-dashed border-line bg-surface px-4 py-12 text-center">
              <p className="text-sm font-medium text-ink">Nada por aquí</p>
              <p className="mt-1 text-sm text-muted">
                Crea la primera orden del taller.
              </p>
              <Link
                href="/panel/nueva-orden"
                className="btn-brand mt-4 inline-flex rounded-md px-4 py-2 text-sm font-semibold"
              >
                Nueva orden
              </Link>
            </li>
          )}
        </ul>
      )}

      <Link
        href="/panel/nueva-orden"
        className="btn-brand fixed bottom-5 right-5 z-40 inline-flex items-center rounded-full px-5 py-3 text-sm font-semibold shadow-lg shadow-black/25 sm:hidden"
      >
        + Nueva
      </Link>

      <p className="mt-6 text-xs text-muted">
        Estados: {statuses.map((s) => s.label).join(" · ")}
      </p>
    </PanelShell>
  );
}

function Stat({
  label,
  value,
  tone = "neutral",
  compact = false,
}: {
  label: string;
  value: number | null;
  tone?: "neutral" | "warn" | "ok";
  compact?: boolean;
}) {
  const toneClass =
    tone === "warn"
      ? "border-[color:var(--warn-line)] bg-warn-soft"
      : tone === "ok"
        ? "border-[color:var(--ok-line)] bg-ok-soft"
        : "border-line bg-surface";
  const labelClass =
    tone === "warn"
      ? "text-[color:var(--warn-ink)]"
      : tone === "ok"
        ? "text-[color:var(--ok-ink)]"
        : "text-muted";
  const valueClass =
    tone === "warn"
      ? "text-[color:var(--warn-ink)]"
      : tone === "ok"
        ? "text-[color:var(--ok-ink)]"
        : "text-ink";

  return (
    <div
      className={`rounded-lg border ${compact ? "px-2 py-2 sm:px-4 sm:py-3" : "px-4 py-3"} ${toneClass}`}
    >
      <p
        className={`font-medium ${labelClass} ${compact ? "text-[10px] leading-tight sm:text-xs" : "text-xs"}`}
      >
        {label}
      </p>
      <p
        className={`mt-0.5 font-[family-name:var(--font-display)] font-bold ${valueClass} ${compact ? "text-lg sm:text-2xl" : "text-2xl"}`}
      >
        {value === null ? "—" : value}
      </p>
    </div>
  );
}
