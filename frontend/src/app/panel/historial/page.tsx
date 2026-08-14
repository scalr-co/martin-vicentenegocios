"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { AuthGuard } from "@/components/auth-guard";
import { PanelShell } from "@/components/panel-shell";
import { PlateHistorySearch } from "@/components/plate-history-search";
import { VehicleHistoryList } from "@/components/vehicle-history-list";
import { errorMessage } from "@/lib/errors";
import { formatVehicleOrItem, type ApiOrder, type ApiVehicle } from "@/lib/types";
import { findVehiclesByPlate, getVehicleHistory } from "@/lib/vehicles";

export default function HistorialPage() {
  return (
    <AuthGuard>
      <Suspense
        fallback={
          <PanelShell title="Historial por patente">
            <p className="text-sm text-muted">Cargando…</p>
          </PanelShell>
        }
      >
        <HistorialContent />
      </Suspense>
    </AuthGuard>
  );
}

function HistorialContent() {
  const searchParams = useSearchParams();
  const plateParam = searchParams.get("plate") ?? "";
  const [vehicle, setVehicle] = useState<ApiVehicle | null>(null);
  const [orders, setOrders] = useState<ApiOrder[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(Boolean(plateParam.trim()));
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const plate = plateParam.trim();
    if (!plate) {
      setVehicle(null);
      setOrders([]);
      setTotal(0);
      setLoading(false);
      setError(null);
      return;
    }

    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const vehicles = await findVehiclesByPlate(plate);
        const found = vehicles[0] ?? null;
        if (cancelled) return;
        setVehicle(found);
        if (!found) {
          setOrders([]);
          setTotal(0);
          return;
        }
        const { data, meta } = await getVehicleHistory(found.id, 1, 50);
        if (cancelled) return;
        const list = Array.isArray(data) ? data : [];
        setOrders(list);
        setTotal(meta?.total ?? list.length);
      } catch (err) {
        if (!cancelled) {
          setError(errorMessage(err, "No se pudo cargar el historial"));
          setVehicle(null);
          setOrders([]);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [plateParam]);

  const subtitle = vehicle
    ? formatVehicleOrItem(vehicle, `Patente ${vehicle.plate}`)
    : "Escribe la patente y ves qué se le hizo antes a ese auto";

  return (
    <PanelShell title="Historial por patente" subtitle={subtitle}>
      <PlateHistorySearch initialPlate={plateParam} />

      {!plateParam.trim() && (
        <p className="mt-4 text-sm text-muted">
          Si el auto ya pasó por el taller, aparecen todas sus órdenes, de la más
          nueva a la más vieja.
        </p>
      )}

      {loading && <p className="mt-4 text-sm text-muted">Buscando…</p>}

      {error && (
        <p role="alert" className="mt-4 text-sm text-red-700">
          {error}
        </p>
      )}

      {!loading && !error && plateParam.trim() && !vehicle && (
        <p className="mt-4 rounded-lg border border-dashed border-line bg-surface px-4 py-8 text-center text-sm text-muted">
          No hay un auto con esa patente en el taller.
        </p>
      )}

      {!loading && vehicle && (
        <div className="mt-6">
          {total > 0 && (
            <p className="mb-3 text-sm text-muted">
              {total} {total === 1 ? "orden" : "órdenes"}
            </p>
          )}
          <VehicleHistoryList orders={orders} />
        </div>
      )}
    </PanelShell>
  );
}
