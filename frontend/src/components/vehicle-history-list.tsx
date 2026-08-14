import Link from "next/link";
import { StatusBadge } from "@/components/ui";
import { formatDateCl } from "@/lib/date";
import { formatVehicleOrItem, type ApiOrder } from "@/lib/types";

export function VehicleHistoryList({
  orders,
  highlightId,
}: {
  orders: ApiOrder[];
  highlightId?: string;
}) {
  if (orders.length === 0) {
    return (
      <p className="rounded-lg border border-dashed border-line bg-surface px-4 py-8 text-center text-sm text-muted">
        Este auto todavía no tiene órdenes en el taller.
      </p>
    );
  }

  return (
    <ul className="space-y-3">
      {orders.map((order) => {
        const vehicleLine =
          order.vehicleOrItem ||
          formatVehicleOrItem(order.vehicle ?? null, "Sin vehículo");
        const current = highlightId && order.id === highlightId;
        return (
          <li key={order.id}>
            <Link
              href={`/panel/ordenes/${order.id}`}
              className={`card-lift block min-w-0 rounded-lg border bg-surface p-4 hover:border-stone-300 ${
                current ? "border-brand" : "border-line"
              }`}
            >
              <div className="flex min-w-0 items-start justify-between gap-2">
                <div className="min-w-0 flex-1 overflow-hidden">
                  <p className="font-semibold text-ink">{order.title}</p>
                  <p className="mt-0.5 truncate text-sm text-muted">
                    {order.client?.name ?? "Cliente"} · {vehicleLine}
                  </p>
                </div>
                <StatusBadge status={order.status} />
              </div>
              {order.createdAt && (
                <p className="mt-3 text-xs text-muted">
                  {formatDateCl(order.createdAt)}
                  {current ? " · esta orden" : ""}
                </p>
              )}
            </Link>
          </li>
        );
      })}
    </ul>
  );
}
