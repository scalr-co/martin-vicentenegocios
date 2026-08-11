"use client";

import { useCallback, useEffect, useState } from "react";
import { AuthGuard } from "@/components/auth-guard";
import { PanelShell } from "@/components/panel-shell";
import { apiList } from "@/lib/api";
import { errorMessage } from "@/lib/errors";
import {
  formatVehicleOrItem,
  type ApiClient,
  type ApiVehicle,
} from "@/lib/types";

export default function ClientesPage() {
  return (
    <AuthGuard>
      <ClientesContent />
    </AuthGuard>
  );
}

function ClientesContent() {
  const [clients, setClients] = useState<ApiClient[]>([]);
  const [vehicles, setVehicles] = useState<ApiVehicle[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [c, v] = await Promise.all([
        apiList<ApiClient>("/clients?limit=50"),
        apiList<ApiVehicle>("/vehicles?limit=100"),
      ]);
      setClients(c);
      setVehicles(v);
      setError(null);
    } catch (err) {
      setError(errorMessage(err, "No se pudieron cargar los clientes"));
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

  return (
    <PanelShell
      title="Clientes"
      subtitle="Clientes y vehículos del taller"
    >
      {loading && <p className="text-sm text-muted">Cargando…</p>}
      {error && (
        <div
          role="alert"
          className="rounded-md border border-red-200 bg-danger-soft px-3 py-3 text-sm text-red-800 dark:text-red-200"
        >
          <p>{error}</p>
          <button
            type="button"
            onClick={() => void load()}
            className="tap-target mt-2 rounded-md border border-red-300 bg-surface px-3 py-1.5 text-sm font-semibold"
          >
            Reintentar
          </button>
        </div>
      )}

      {!loading && !error && (
        <ul className="space-y-3">
          {clients.map((client) => {
            const clientVehicles = vehicles.filter(
              (v) => v.clientId === client.id,
            );
            return (
              <li
                key={client.id}
                className="card-lift min-w-0 rounded-lg border border-line bg-surface p-4"
              >
                <div className="flex min-w-0 flex-wrap items-start justify-between gap-2">
                  <div className="min-w-0 overflow-hidden">
                    <p className="truncate font-semibold text-ink">
                      {client.name}
                    </p>
                    <p className="text-sm text-muted">{client.phone}</p>
                    {client.notes && (
                      <p className="mt-1 text-xs text-muted">{client.notes}</p>
                    )}
                  </div>
                </div>
                <div className="mt-4 border-t border-line pt-3">
                  <p className="text-xs font-semibold uppercase tracking-wide text-muted">
                    Vehículos
                  </p>
                  <ul className="mt-2 space-y-1.5">
                    {clientVehicles.map((v) => (
                      <li key={v.id} className="text-sm text-ink">
                        {formatVehicleOrItem(v)}
                      </li>
                    ))}
                    {clientVehicles.length === 0 && (
                      <li className="text-sm text-muted">Sin vehículos</li>
                    )}
                  </ul>
                </div>
              </li>
            );
          })}
          {clients.length === 0 && (
            <li className="rounded-lg border border-dashed border-line bg-surface px-4 py-10 text-center text-sm text-muted">
              Aún no hay clientes. Crea uno al armar una orden nueva.
            </li>
          )}
        </ul>
      )}
    </PanelShell>
  );
}
