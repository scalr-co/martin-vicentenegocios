export type WorkshopAccountStatus = "active" | "suspended" | "deleted";

export type WorkshopAccount = {
  id: string;
  name: string;
  ownerName: string;
  email: string;
  phone: string;
  status: WorkshopAccountStatus;
  suspendedUntil?: string | null;
  createdAt: string;
};

const STORAGE_KEY = "motorping_admin_accounts_demo";

/** Cuentas demo locales hasta que exista la API de admin. */
const SEED: WorkshopAccount[] = [
  {
    id: "ws_demo_1",
    name: "Taller El Pino",
    ownerName: "Carlos Pérez",
    email: "carlos@elpino.cl",
    phone: "56911111111",
    status: "active",
    createdAt: "2026-07-12",
  },
  {
    id: "ws_demo_2",
    name: "Desabolladura Sur",
    ownerName: "Ana Rojas",
    email: "ana@desabolladurasur.cl",
    phone: "56922222222",
    status: "suspended",
    suspendedUntil: "2026-09-01",
    createdAt: "2026-06-03",
  },
];

function readAll(): WorkshopAccount[] {
  if (typeof window === "undefined") return SEED;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(SEED));
      return SEED;
    }
    return JSON.parse(raw) as WorkshopAccount[];
  } catch {
    return SEED;
  }
}

function writeAll(list: WorkshopAccount[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
}

export function listWorkshopAccounts(): WorkshopAccount[] {
  return readAll().filter((a) => a.status !== "deleted");
}

export function countWorkshopAccounts() {
  const list = listWorkshopAccounts();
  return {
    total: list.length,
    active: list.filter((a) => a.status === "active").length,
    suspended: list.filter((a) => a.status === "suspended").length,
  };
}

export function createWorkshopAccount(input: {
  name: string;
  ownerName: string;
  email: string;
  phone: string;
  password: string;
}): WorkshopAccount {
  void input.password;
  const next: WorkshopAccount = {
    id: `ws_${Date.now()}`,
    name: input.name.trim(),
    ownerName: input.ownerName.trim(),
    email: input.email.trim().toLowerCase(),
    phone: input.phone.replace(/\D/g, ""),
    status: "active",
    createdAt: new Date().toISOString().slice(0, 10),
  };
  const list = readAll();
  writeAll([next, ...list]);
  return next;
}

export function suspendWorkshopAccount(id: string, days: number) {
  const until = new Date();
  until.setDate(until.getDate() + days);
  const list = readAll().map((a) =>
    a.id === id
      ? {
          ...a,
          status: "suspended" as const,
          suspendedUntil: until.toISOString().slice(0, 10),
        }
      : a,
  );
  writeAll(list);
}

export function reactivateWorkshopAccount(id: string) {
  const list = readAll().map((a) =>
    a.id === id
      ? { ...a, status: "active" as const, suspendedUntil: null }
      : a,
  );
  writeAll(list);
}

export function deleteWorkshopAccount(id: string) {
  const list = readAll().map((a) =>
    a.id === id ? { ...a, status: "deleted" as const } : a,
  );
  writeAll(list);
}
