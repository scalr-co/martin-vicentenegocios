import type { WorkshopPlan } from "@/lib/plans";

export type WorkshopAccountStatus = "active" | "suspended" | "deleted";

export type WorkshopAccount = {
  id: string;
  name: string;
  ownerName: string;
  email: string;
  phone: string;
  plan: WorkshopPlan;
  status: WorkshopAccountStatus;
  /** Fecha fin suspensión; null = indefinida (hasta que la reactivemos). */
  suspendedUntil?: string | null;
  suspendIndefinite?: boolean;
  createdAt: string;
};

const STORAGE_KEY = "motorping_admin_accounts_demo_v2";

const SEED: WorkshopAccount[] = [
  {
    id: "ws_demo_1",
    name: "Taller El Pino",
    ownerName: "Carlos Pérez",
    email: "carlos@elpino.cl",
    phone: "56911111111",
    plan: "basico",
    status: "active",
    createdAt: "2026-07-12",
  },
  {
    id: "ws_demo_2",
    name: "Desabolladura Sur",
    ownerName: "Ana Rojas",
    email: "ana@desabolladurasur.cl",
    phone: "56922222222",
    plan: "plus",
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
    const parsed = JSON.parse(raw) as WorkshopAccount[];
    return parsed.map((a) => ({
      ...a,
      plan: a.plan === "plus" ? "plus" : "basico",
    }));
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

export function getWorkshopAccount(id: string): WorkshopAccount | null {
  return listWorkshopAccounts().find((a) => a.id === id) ?? null;
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
  plan: WorkshopPlan;
}): WorkshopAccount {
  void input.password;
  const next: WorkshopAccount = {
    id: `ws_${Date.now()}`,
    name: input.name.trim(),
    ownerName: input.ownerName.trim(),
    email: input.email.trim().toLowerCase(),
    phone: input.phone.replace(/\D/g, ""),
    plan: input.plan,
    status: "active",
    createdAt: new Date().toISOString().slice(0, 10),
  };
  writeAll([next, ...readAll()]);
  return next;
}

export type SuspendOption = 7 | 14 | 21 | 31 | "indefinite";

export function suspendWorkshopAccount(id: string, option: SuspendOption) {
  const list = readAll().map((a) => {
    if (a.id !== id) return a;
    if (option === "indefinite") {
      return {
        ...a,
        status: "suspended" as const,
        suspendIndefinite: true,
        suspendedUntil: null,
      };
    }
    const until = new Date();
    until.setDate(until.getDate() + option);
    return {
      ...a,
      status: "suspended" as const,
      suspendIndefinite: false,
      suspendedUntil: until.toISOString().slice(0, 10),
    };
  });
  writeAll(list);
}

export function reactivateWorkshopAccount(id: string) {
  const list = readAll().map((a) =>
    a.id === id
      ? {
          ...a,
          status: "active" as const,
          suspendedUntil: null,
          suspendIndefinite: false,
        }
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
