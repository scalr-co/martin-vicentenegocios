import { apiDownload, apiFetch } from "@/lib/api";
import { formatDateCl } from "@/lib/date";
import { getWorkshopPlan } from "@/lib/mechanics";
import { statusLabel } from "@/lib/statuses";

export function isPlusPlan() {
  return getWorkshopPlan() === "plus";
}

/** Contrato GET /reports/weekly — lo arma el backend. */
export type WeeklyReport = {
  workshopName: string;
  from: string;
  to: string;
  ordersOpen: number;
  ordersWaiting: number;
  ordersReady: number;
  ordersCreated: number;
  ordersDelivered: number;
  byStatus: { status: string; count: number }[];
  openOrders: { id: string; title: string; status: string }[];
};

export type WeeklySummary = {
  workshop: string;
  fromLabel: string;
  toLabel: string;
  openNow: number;
  waiting: number;
  ready: number;
  createdThisWeek: number;
  deliveredThisWeek: number;
  byStatus: { status: string; label: string; count: number }[];
  openTitles: string[];
};

export async function buildWeeklySummary(): Promise<WeeklySummary> {
  const { data } = await apiFetch<WeeklyReport>("/reports/weekly");
  return {
    workshop: data.workshopName,
    fromLabel: formatDateCl(data.from) || data.from,
    toLabel: formatDateCl(data.to) || data.to,
    openNow: data.ordersOpen,
    waiting: data.ordersWaiting,
    ready: data.ordersReady,
    createdThisWeek: data.ordersCreated,
    deliveredThisWeek: data.ordersDelivered,
    byStatus: (data.byStatus ?? []).map((s) => ({
      status: s.status,
      label: statusLabel(s.status),
      count: s.count,
    })),
    openTitles: (data.openOrders ?? []).slice(0, 8).map((o) => o.title),
  };
}

export async function exportClientsAndHistoryCsv() {
  await apiDownload("/exports/clients", "clientes.csv");
  await apiDownload("/exports/history", "historial.csv");
}
