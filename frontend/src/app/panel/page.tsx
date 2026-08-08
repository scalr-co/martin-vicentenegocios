"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { AuthGuard } from "@/components/auth-guard";
import { PanelShell } from "@/components/panel-shell";
import { StatusBadge } from "@/components/ui";
import { apiList } from "@/lib/api";
import {
  formatVehicleOrItem,
  statusLabel,
  type ApiOrder,
} from "@/lib/types";

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

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        setLoading(true);
        const list = await apiList<ApiOrder>("/orders?open=true&limit=50");
        if (!cancelled) {
          setOrders(list.map(normalizeOrder));
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Error al cargar");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const waiting = orders.filter(
    (o) =>
      o.status === "esperando_aprobacion" || o.status === "esperando_repuesto",
  );
  const ready = orders.filter((o) => o.status === "listo");

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
      <div className="mb-6 grid gap-3 sm:grid-cols-3">
        <Stat label="Abiertas" value={orders.length} />
        <Stat
          label="Esperando cliente/repuesto"
          value={waiting.length}
          tone="warn"
        />
        <Stat label="Listos para retirar" value={ready.length} tone="ok" />
      </div>

      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap gap-1.5">
          {FILTERS.map((f) => (
            <button
              key={f.id}
              type="button"
              onClick={() => setFilter(f.id)}
              className={`rounded-full px-3 py-1.5 text-xs font-medium transition ${
                filter === f.id
                  ? "bg-steel text-white"
                  : "bg-white text-muted ring-1 ring-line hover:text-ink"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
        <Link
          href="/panel/nueva-orden"
          className="hidden rounded-md bg-brand px-4 py-2 text-sm font-semibold text-white hover:bg-brand-dark sm:inline-flex"
        >
          Nueva orden
        </Link>
      </div>

      {loading && <p className="text-sm text-muted">Cargando órdenes…</p>}
      {error && (
        <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
          {error}
        </p>
      )}

      {!loading && !error && (
        <ul className="space-y-3 pb-20 sm:pb-0">
          {visible.map((order) => (
            <li key={order.id}>
              <Link
                href={`/panel/ordenes/${order.id}`}
                className="card-lift block rounded-lg border border-line bg-surface p-4 hover:border-stone-300"
              >
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div className="min-w-0 flex-1">
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
                    Estimado: {order.estimatedAt}
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
                className="mt-4 inline-flex rounded-md bg-brand px-4 py-2 text-sm font-semibold text-white hover:bg-brand-dark"
              >
                Nueva orden
              </Link>
            </li>
          )}
        </ul>
      )}

      <Link
        href="/panel/nueva-orden"
        className="fixed bottom-5 right-5 z-40 inline-flex items-center rounded-full bg-brand px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-orange-900/20 hover:bg-brand-dark sm:hidden"
      >
        + Nueva
      </Link>

      <p className="mt-6 text-xs text-muted">
        Estados:{" "}
        {[
          "recibido",
          "en_diagnostico",
          "esperando_aprobacion",
          "en_reparacion",
          "esperando_repuesto",
          "listo",
          "entregado",
        ]
          .map(statusLabel)
          .join(" · ")}
      </p>
    </PanelShell>
  );
}

function Stat({
  label,
  value,
  tone = "neutral",
}: {
  label: string;
  value: number;
  tone?: "neutral" | "warn" | "ok";
}) {
  const toneClass =
    tone === "warn"
      ? "border-amber-200 bg-amber-50"
      : tone === "ok"
        ? "border-emerald-200 bg-emerald-50"
        : "border-line bg-surface";

  return (
    <div className={`rounded-lg border px-4 py-3 ${toneClass}`}>
      <p className="text-xs font-medium text-muted">{label}</p>
      <p className="mt-1 font-[family-name:var(--font-display)] text-2xl font-bold text-ink">
        {value}
      </p>
    </div>
  );
}
