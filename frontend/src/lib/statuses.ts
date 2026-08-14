import { apiList } from "@/lib/api";

/** GET /statuses — EstadoDeOrdenSalida */
export type OrderStatusInfo = {
  key: string;
  label: string;
  isOpen: boolean;
};

const FALLBACK: OrderStatusInfo[] = [
  { key: "recibido", label: "Recibido", isOpen: true },
  { key: "en_diagnostico", label: "En diagnóstico", isOpen: true },
  { key: "esperando_aprobacion", label: "Esperando aprobación", isOpen: true },
  { key: "en_reparacion", label: "En reparación", isOpen: true },
  { key: "esperando_repuesto", label: "Esperando repuesto", isOpen: true },
  { key: "listo", label: "Listo", isOpen: true },
  { key: "entregado", label: "Entregado", isOpen: false },
];

let cache: OrderStatusInfo[] | null = null;
const listeners = new Set<() => void>();

function notify() {
  listeners.forEach((fn) => fn());
}

export function subscribeStatuses(listener: () => void) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function getStatuses(): OrderStatusInfo[] {
  return cache ?? FALLBACK;
}

export async function loadStatuses(): Promise<OrderStatusInfo[]> {
  const list = await apiList<OrderStatusInfo>("/statuses");
  if (list.length > 0) {
    cache = list;
    notify();
  }
  return getStatuses();
}

export function statusLabel(status: string) {
  return getStatuses().find((s) => s.key === status)?.label ?? status;
}
