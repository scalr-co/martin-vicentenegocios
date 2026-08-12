import { getWorkshop } from "@/lib/auth";
import type { WorkshopPlan } from "@/lib/plans";
import { MAX_MECHANICS_BASIC } from "@/lib/plans";

export type Mechanic = {
  id: string;
  name: string;
  email: string;
  phone: string;
  notes?: string | null;
  createdAt: string;
};

const STORAGE_KEY = "motorping_mechanics_demo";
const PLAN_KEY = "motorping_demo_plan";

/** Plan del taller en sesión (demo local hasta que la API lo envíe). */
export function getWorkshopPlan(): WorkshopPlan {
  const fromWorkshop = getWorkshop()?.plan;
  if (fromWorkshop === "plus" || fromWorkshop === "basico") return fromWorkshop;
  if (typeof window === "undefined") return "basico";
  try {
    const raw = localStorage.getItem(PLAN_KEY);
    if (raw === "plus" || raw === "basico") return raw;
  } catch {
    // ignore
  }
  return "basico";
}

export function setDemoWorkshopPlan(plan: WorkshopPlan) {
  localStorage.setItem(PLAN_KEY, plan);
}

function readAll(): Mechanic[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    return JSON.parse(raw) as Mechanic[];
  } catch {
    return [];
  }
}

function writeAll(list: Mechanic[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
}

export function listMechanics(): Mechanic[] {
  return readAll().sort((a, b) => a.name.localeCompare(b.name, "es"));
}

export function getMechanic(id: string): Mechanic | null {
  return readAll().find((m) => m.id === id) ?? null;
}

export function canAddMechanic(plan: WorkshopPlan = getWorkshopPlan()): {
  ok: boolean;
  reason?: string;
} {
  const count = listMechanics().length;
  if (plan === "basico" && count >= MAX_MECHANICS_BASIC) {
    return {
      ok: false,
      reason: `El plan Básico permite hasta ${MAX_MECHANICS_BASIC} mecánicos. Pasa a Plus para agregar más.`,
    };
  }
  return { ok: true };
}

export function createMechanic(input: {
  name: string;
  email: string;
  phone: string;
  notes?: string;
  password?: string;
}): Mechanic {
  void input.password;
  const gate = canAddMechanic();
  if (!gate.ok) throw new Error(gate.reason);

  const next: Mechanic = {
    id: `mec_${Date.now()}`,
    name: input.name.trim(),
    email: input.email.trim().toLowerCase(),
    phone: input.phone.replace(/\D/g, ""),
    notes: input.notes?.trim() || null,
    createdAt: new Date().toISOString().slice(0, 10),
  };
  writeAll([next, ...readAll()]);
  return next;
}

export function updateMechanic(
  id: string,
  patch: Partial<Pick<Mechanic, "name" | "email" | "phone" | "notes">>,
): Mechanic | null {
  let updated: Mechanic | null = null;
  const list = readAll().map((m) => {
    if (m.id !== id) return m;
    updated = {
      ...m,
      name: patch.name !== undefined ? patch.name.trim() : m.name,
      email:
        patch.email !== undefined ? patch.email.trim().toLowerCase() : m.email,
      phone:
        patch.phone !== undefined ? patch.phone.replace(/\D/g, "") : m.phone,
      notes:
        patch.notes !== undefined
          ? (patch.notes?.trim() || null)
          : m.notes,
    };
    return updated;
  });
  writeAll(list);
  return updated;
}

export function deleteMechanic(id: string) {
  writeAll(readAll().filter((m) => m.id !== id));
}
