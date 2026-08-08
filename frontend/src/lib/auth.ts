const TOKEN_KEY = "tallertrack_token";
const WORKSHOP_KEY = "tallertrack_workshop";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setSession(token: string, workshop?: unknown) {
  localStorage.setItem(TOKEN_KEY, token);
  if (workshop) {
    localStorage.setItem(WORKSHOP_KEY, JSON.stringify(workshop));
  }
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(WORKSHOP_KEY);
}

export function getWorkshopName(): string {
  if (typeof window === "undefined") return "Taller";
  try {
    const raw = localStorage.getItem(WORKSHOP_KEY);
    if (!raw) return "Taller";
    const parsed = JSON.parse(raw) as { name?: string };
    return parsed.name ?? "Taller";
  } catch {
    return "Taller";
  }
}
