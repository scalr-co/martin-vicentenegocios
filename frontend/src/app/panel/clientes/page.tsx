"use client";

import { useEffect, useState } from "react";
import { AuthGuard } from "@/components/auth-guard";
import { PanelShell } from "@/components/panel-shell";
import { apiList } from "@/lib/api";
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

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        setLoading(true);
        const [c, v] = await Promise.all([
          apiList<ApiClient>("/clients?limit=50"),
          apiList<ApiVehicle>("/vehicles?limit=100"),
        ]);
        if (!cancelled) {
          setClients(c);
          setVehicles(v);
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

  return (
    <PanelShell
      title="Clientes"
      subtitle="Clientes y vehículos del taller"
    >
      {loading && <p className="text-sm text-muted">Cargando…</p>}
      {error && (
        <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
          {error}
        </p>
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
                className="card-lift rounded-lg border border-line bg-surface p-4"
              >
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div>
                    <p className="font-semibold text-ink">{client.name}</p>
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
