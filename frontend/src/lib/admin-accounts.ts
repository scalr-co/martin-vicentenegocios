import { apiFetch, apiList } from "@/lib/api";
import type { WorkshopPlan } from "@/lib/plans";

export type WorkshopAccountStatus = "active" | "suspended" | "deleted";

/** TallerEnLista / FichaDeTaller (openapi). */
export type WorkshopAccount = {
  id: string;
  name: string;
  phone: string;
  whatsappMode?: string;
  plan: WorkshopPlan | string;
  active: boolean;
  status: WorkshopAccountStatus | string;
  suspendedUntil: string | null;
  suspendIndefinite: boolean;
  ownerEmail?: string | null;
  ordersCount?: number;
  createdAt?: string;
  deletedAt?: string | null;
  stats?: {
    ordersTotal?: number;
    ordersOpen?: number;
    lastActivityAt?: string | null;
    noticesPending?: number;
    usersActive?: number;
  };
};

export type SuspendOption = 7 | 14 | 21 | 31 | "indefinite";

function asPlan(plan: unknown): WorkshopPlan {
  return plan === "plus" ? "plus" : "basico";
}

function normalizeWorkshop(raw: WorkshopAccount): WorkshopAccount {
  return {
    ...raw,
    plan: asPlan(raw.plan),
    suspendedUntil: raw.suspendedUntil ?? null,
    suspendIndefinite: Boolean(raw.suspendIndefinite),
    active: Boolean(raw.active),
  };
}

export async function listWorkshopAccounts(
  opts: { archived?: boolean } = {},
): Promise<WorkshopAccount[]> {
  const path = opts.archived
    ? "/admin/workshops?archived=true"
    : "/admin/workshops";
  const list = await apiList<WorkshopAccount>(path);
  return list.map(normalizeWorkshop);
}

export async function getWorkshopAccount(
  id: string,
): Promise<WorkshopAccount | null> {
  try {
    const { data } = await apiFetch<WorkshopAccount>(`/admin/workshops/${id}`);
    return normalizeWorkshop(data);
  } catch (err) {
    const status = (err as { status?: number })?.status;
    if (status === 404) return null;
    throw err;
  }
}

export function countWorkshopAccounts(list: WorkshopAccount[]) {
  return {
    total: list.length,
    active: list.filter((a) => a.status === "active").length,
    suspended: list.filter((a) => a.status === "suspended").length,
  };
}

export async function createWorkshopAccount(input: {
  workshopName: string;
  workshopPhone: string;
  ownerName: string;
  email: string;
  password: string;
  plan: WorkshopPlan;
}): Promise<WorkshopAccount> {
  const { data } = await apiFetch<WorkshopAccount>("/admin/workshops", {
    method: "POST",
    body: JSON.stringify({
      workshopName: input.workshopName.trim(),
      workshopPhone: input.workshopPhone.replace(/\D/g, ""),
      ownerName: input.ownerName.trim(),
      email: input.email.trim().toLowerCase(),
      password: input.password,
      plan: input.plan,
    }),
  });
  return normalizeWorkshop(data);
}

function suspendUntilIso(days: number): string {
  const until = new Date();
  until.setUTCDate(until.getUTCDate() + days);
  until.setUTCHours(0, 0, 0, 0);
  return until.toISOString();
}

export async function suspendWorkshopAccount(
  id: string,
  option: SuspendOption,
): Promise<WorkshopAccount> {
  const body =
    option === "indefinite"
      ? { active: false }
      : { active: false, suspendedUntil: suspendUntilIso(option) };
  const { data } = await apiFetch<WorkshopAccount>(`/admin/workshops/${id}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
  return normalizeWorkshop(data);
}

export async function reactivateWorkshopAccount(
  id: string,
): Promise<WorkshopAccount> {
  const { data } = await apiFetch<WorkshopAccount>(`/admin/workshops/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ active: true }),
  });
  return normalizeWorkshop(data);
}

export async function deleteWorkshopAccount(id: string): Promise<void> {
  await apiFetch(`/admin/workshops/${id}`, { method: "DELETE" });
}

export async function restoreWorkshopAccount(
  id: string,
): Promise<WorkshopAccount> {
  const { data } = await apiFetch<WorkshopAccount>(
    `/admin/workshops/${id}/restore`,
    { method: "POST" },
  );
  return normalizeWorkshop(data);
}

export async function patchWorkshopPlan(
  id: string,
  plan: WorkshopPlan,
): Promise<WorkshopAccount> {
  const { data } = await apiFetch<WorkshopAccount>(`/admin/workshops/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ plan }),
  });
  return normalizeWorkshop(data);
}
