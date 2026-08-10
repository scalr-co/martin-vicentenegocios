const TOKEN_KEY = "tallertrack_token";
const WORKSHOP_KEY = "tallertrack_workshop";
const USER_KEY = "tallertrack_user";

export type SessionWorkshop = {
  id?: string;
  name?: string;
  phone?: string;
};

export type SessionUser = {
  id?: string;
  email?: string;
  name?: string;
  role?: "admin" | "owner" | "mechanic" | string;
};

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setSession(
  token: string,
  workshop?: unknown,
  user?: unknown,
) {
  localStorage.setItem(TOKEN_KEY, token);
  if (workshop) {
    localStorage.setItem(WORKSHOP_KEY, JSON.stringify(workshop));
  }
  if (user) {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  }
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(WORKSHOP_KEY);
  localStorage.removeItem(USER_KEY);
}

export function getWorkshop(): SessionWorkshop | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(WORKSHOP_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as SessionWorkshop;
  } catch {
    return null;
  }
}

export function getWorkshopName(): string {
  return getWorkshop()?.name?.trim() || "Taller";
}

export function getUser(): SessionUser | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(USER_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as SessionUser;
  } catch {
    return null;
  }
}

/** Admin de plataforma (Martín / Vicente), no dueño de un taller. */
export function isAdmin(): boolean {
  const user = getUser();
  const role = (user?.role || "").toLowerCase();
  if (role === "admin" || role === "superadmin" || role === "platform_admin") {
    return true;
  }
  const email = (user?.email || "").toLowerCase();
  // Fallback temporal hasta que la API marque el rol.
  return (
    email.endsWith("@tallertrack.cl") &&
    (email.startsWith("admin") ||
      email.startsWith("martin") ||
      email.startsWith("vicente") ||
      email.startsWith("solve"))
  );
}

export function extractSessionFromLogin(data: Record<string, unknown>): {
  workshop: SessionWorkshop | null;
  user: SessionUser | null;
} {
  const workshopRaw =
    (data.workshop as SessionWorkshop | undefined) ||
    ((data.data as Record<string, unknown> | undefined)?.workshop as
      | SessionWorkshop
      | undefined) ||
    null;

  const userRaw =
    (data.user as SessionUser | undefined) ||
    ((data.data as Record<string, unknown> | undefined)?.user as
      | SessionUser
      | undefined) ||
    null;

  const workshop: SessionWorkshop | null = workshopRaw
    ? {
        id: workshopRaw.id,
        name: workshopRaw.name,
        phone: workshopRaw.phone,
      }
    : null;

  const user: SessionUser | null = userRaw
    ? {
        id: userRaw.id,
        email: userRaw.email,
        name: userRaw.name,
        role: userRaw.role,
      }
    : data.email
      ? { email: String(data.email), role: String(data.role || "") }
      : null;

  return { workshop, user };
}
