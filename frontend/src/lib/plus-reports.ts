import { apiList } from "@/lib/api";
import { getWorkshop, getWorkshopName } from "@/lib/auth";
import { formatDateCl } from "@/lib/date";
import { getWorkshopPlan } from "@/lib/mechanics";
import { downloadCsv, toCsv } from "@/lib/csv";
import {
  formatVehicleOrItem,
  statusLabel,
  type ApiClient,
  type ApiOrder,
  type ApiVehicle,
} from "@/lib/types";

export function isPlusPlan() {
  return getWorkshopPlan() === "plus";
}

function startOfWeek(d: Date) {
  const start = new Date(d);
  start.setHours(0, 0, 0, 0);
  const day = start.getDay();
  const diff = day === 0 ? 6 : day - 1;
  start.setDate(start.getDate() - diff);
  return start;
}

function endOfWeek(start: Date) {
  const end = new Date(start);
  end.setDate(end.getDate() + 6);
  end.setHours(23, 59, 59, 999);
  return end;
}

function inRange(iso: string | undefined, from: Date, to: Date) {
  if (!iso) return false;
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return false;
  return d >= from && d <= to;
}

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
  const from = startOfWeek(new Date());
  const to = endOfWeek(from);
  const [open, recent] = await Promise.all([
    apiList<ApiOrder>("/orders?open=true&limit=100"),
    apiList<ApiOrder>("/orders?limit=100"),
  ]);

  const waiting = open.filter(
    (o) =>
      o.status === "esperando_aprobacion" || o.status === "esperando_repuesto",
  ).length;
  const ready = open.filter((o) => o.status === "listo").length;
  const createdThisWeek = recent.filter((o) =>
    inRange(o.createdAt, from, to),
  );
  const deliveredThisWeek = recent.filter(
    (o) => o.status === "entregado" && inRange(o.createdAt, from, to),
  ).length;

  const counts = new Map<string, number>();
  for (const o of createdThisWeek) {
    counts.set(o.status, (counts.get(o.status) || 0) + 1);
  }

  return {
    workshop: getWorkshopName(),
    fromLabel: formatDateCl(from.toISOString()),
    toLabel: formatDateCl(to.toISOString()),
    openNow: open.length,
    waiting,
    ready,
    createdThisWeek: createdThisWeek.length,
    deliveredThisWeek,
    byStatus: [...counts.entries()]
      .sort((a, b) => b[1] - a[1])
      .map(([status, count]) => ({
        status,
        label: statusLabel(status),
        count,
      })),
    openTitles: open.slice(0, 8).map((o) => o.title),
  };
}

export async function exportClientsAndHistoryCsv() {
  const [clients, vehicles, orders] = await Promise.all([
    apiList<ApiClient>("/clients?limit=100"),
    apiList<ApiVehicle>("/vehicles?limit=100"),
    apiList<ApiOrder>("/orders?limit=100"),
  ]);

  const plateByClient = new Map<string, string[]>();
  const vehicleByClient = new Map<string, string[]>();
  for (const v of vehicles) {
    if (!v.clientId) continue;
    const plates = plateByClient.get(v.clientId) ?? [];
    plates.push(v.plate);
    plateByClient.set(v.clientId, plates);
    const lines = vehicleByClient.get(v.clientId) ?? [];
    lines.push(formatVehicleOrItem(v));
    vehicleByClient.set(v.clientId, lines);
  }

  const clientsCsv = toCsv(
    ["Nombre", "WhatsApp", "RUT", "Notas", "Patentes", "Vehículos"],
    clients.map((c) => [
      c.name,
      c.phone,
      c.rut ?? "",
      c.notes ?? "",
      (plateByClient.get(c.id) ?? []).join(" | "),
      (vehicleByClient.get(c.id) ?? []).join(" | "),
    ]),
  );

  const historyCsv = toCsv(
    [
      "Fecha",
      "Título",
      "Estado",
      "Cliente",
      "WhatsApp",
      "Vehículo",
      "Estimado",
    ],
    orders.map((o) => [
      formatDateCl(o.createdAt) || o.createdAt || "",
      o.title,
      statusLabel(o.status),
      o.client?.name ?? "",
      o.client?.phone ?? "",
      o.vehicleOrItem || formatVehicleOrItem(o.vehicle ?? null),
      formatDateCl(o.estimatedAt) || "",
    ]),
  );

  const stamp = new Date().toISOString().slice(0, 10);
  const slug = (getWorkshop()?.name || "taller")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
  downloadCsv(`${slug || "taller"}-clientes-${stamp}.csv`, clientsCsv);
  downloadCsv(`${slug || "taller"}-historial-${stamp}.csv`, historyCsv);
}
