"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useSyncExternalStore } from "react";
import { BrandMarkIcon } from "@/components/ui";
import { clearSession, getWorkshopName, isAdmin, isOwner } from "@/lib/auth";
import { loadStatuses } from "@/lib/statuses";

type LeaveGuardValue = {
  setLeaveBlocked: (blocked: boolean) => void;
  requestNavigate: (href: string, e?: React.MouseEvent) => void;
};

const LeaveGuardContext = createContext<LeaveGuardValue | null>(null);

export function useLeaveGuard() {
  return useContext(LeaveGuardContext);
}

/** Registra bloqueo al salir (ej. WhatsApp sin enviar). */
export function useLeaveBlock(blocked: boolean) {
  const ctx = useLeaveGuard();
  useEffect(() => {
    ctx?.setLeaveBlocked(blocked);
    return () => ctx?.setLeaveBlocked(false);
  }, [blocked, ctx]);
}

const links = [
  { href: "/panel", label: "Hoy", exact: true },
  { href: "/panel/historial", label: "Historial", exact: false },
  { href: "/panel/clientes", label: "Clientes", exact: false },
  { href: "/panel/nueva-orden", label: "Nueva orden", exact: false },
];

function NavLink({
  href,
  label,
  exact,
  onNavigate,
}: {
  href: string;
  label: string;
  exact: boolean;
  onNavigate: (href: string, e: React.MouseEvent) => void;
}) {
  const pathname = usePathname();
  const active = exact ? pathname === href : pathname.startsWith(href);

  return (
    <Link
      href={href}
      onClick={(e) => onNavigate(href, e)}
      className={`tap-target inline-flex items-center rounded-md px-3 py-1.5 text-sm transition ${
        active
          ? "bg-brand text-brand-ink"
          : "text-muted hover:bg-chip hover:text-ink"
      }`}
    >
      {label}
    </Link>
  );
}

function useClientFlag(read: () => boolean) {
  return useSyncExternalStore(
    () => () => {},
    read,
    () => false,
  );
}

function useClientWorkshopName() {
  return useSyncExternalStore(
    () => () => {},
    () => getWorkshopName(),
    () => "Taller",
  );
}

export function PanelShell({
  title,
  subtitle,
  headerAction,
  children,
}: {
  title: string;
  subtitle?: string;
  headerAction?: React.ReactNode;
  children: React.ReactNode;
}) {
  const router = useRouter();
  const workshop = useClientWorkshopName();
  const admin = useClientFlag(() => isAdmin());
  const owner = useClientFlag(() => isOwner());
  const pathname = usePathname();
  const adminActive = pathname.startsWith("/panel/admin");

  const [leaveBlocked, setLeaveBlocked] = useState(false);
  const [leaveConfirmOpen, setLeaveConfirmOpen] = useState(false);
  const [pendingHref, setPendingHref] = useState<string | null>(null);
  const [logoutConfirmOpen, setLogoutConfirmOpen] = useState(false);

  useEffect(() => {
    void loadStatuses().catch(() => {
      /* etiquetas de respaldo en statuses.ts */
    });
  }, []);

  const requestNavigate = useCallback(
    (href: string, e?: React.MouseEvent) => {
      if (leaveBlocked && href !== pathname) {
        e?.preventDefault();
        setPendingHref(href);
        setLeaveConfirmOpen(true);
        return;
      }
    },
    [leaveBlocked, pathname],
  );

  const leaveGuard = useMemo(
    () => ({ setLeaveBlocked, requestNavigate }),
    [requestNavigate],
  );

  const nav = admin
    ? [{ href: "/panel/admin", label: "Admin", exact: false as const }]
    : [
        ...links,
        ...(owner
          ? [
              {
                href: "/panel/mecanicos",
                label: "Mecánicos",
                exact: false as const,
              },
            ]
          : []),
      ];

  function confirmLeave() {
    const href = pendingHref || "/panel";
    setLeaveConfirmOpen(false);
    setPendingHref(null);
    setLeaveBlocked(false);
    router.push(href);
  }

  function doLogout() {
    clearSession();
    router.replace("/login");
  }

  return (
    <LeaveGuardContext.Provider value={leaveGuard}>
      <div className="flex min-h-dvh w-full min-w-0 flex-1 flex-col bg-background text-ink">
        <header className="sticky top-0 z-30 border-b border-line bg-surface/95 backdrop-blur">
          <div
            className="h-0.5 w-full"
            style={{
              background:
                "linear-gradient(90deg, transparent, var(--brand), transparent)",
            }}
            aria-hidden
          />
          <div className="mx-auto flex w-full min-w-0 max-w-5xl items-center justify-between gap-3 px-4 py-2 sm:gap-4 sm:py-3">
            <div className="flex min-w-0 items-center gap-4 sm:gap-6">
              <Link
                href={admin ? "/panel/admin" : "/panel"}
                className="min-w-0"
                onClick={(e) =>
                  requestNavigate(admin ? "/panel/admin" : "/panel", e)
                }
              >
                <span className="flex min-w-0 items-center gap-2">
                  <BrandMarkIcon size={22} className="shrink-0" />
                  <span className="block min-w-0 truncate font-[family-name:var(--font-display)] text-base font-bold tracking-tight text-ink sm:text-lg">
                    {admin ? "Motor Ping Admin" : workshop}
                  </span>
                </span>
                {!admin && (
                  <span className="mt-0.5 block pl-7 text-[10px] font-medium uppercase tracking-[0.14em] text-muted">
                    Motor Ping
                  </span>
                )}
              </Link>
              <nav className="hidden items-center gap-1 sm:flex">
                {nav.map((link) => (
                  <NavLink
                    key={link.href}
                    {...link}
                    onNavigate={requestNavigate}
                  />
                ))}
              </nav>
            </div>
            <div className="flex shrink-0 items-center gap-3 sm:gap-4">
              <div className="hidden text-right sm:block">
                <p className="text-xs font-medium text-ink">
                  {admin ? "Administración" : workshop}
                </p>
                <p className="text-[11px] text-muted">
                  {admin ? "Cuentas de talleres" : "Modo WhatsApp: link"}
                </p>
              </div>
              <button
                type="button"
                onClick={() => setLogoutConfirmOpen(true)}
                className="tap-target inline-flex min-w-[44px] items-center justify-center rounded-md px-3 text-sm text-muted hover:bg-chip hover:text-ink"
              >
                Salir
              </button>
            </div>
          </div>
          <nav className="flex gap-1 overflow-x-auto border-t border-line px-4 py-1.5 sm:hidden">
            {nav.map((link) => (
              <NavLink
                key={link.href}
                {...link}
                onNavigate={requestNavigate}
              />
            ))}
            {admin && (
              <span className="sr-only">
                {adminActive ? "Admin activo" : "Admin"}
              </span>
            )}
          </nav>
        </header>

        <main className="mx-auto w-full min-w-0 max-w-5xl flex-1 px-4 py-4 pb-24 sm:py-8 sm:pb-10">
          <div className="flex min-w-0 flex-wrap items-end justify-between gap-3">
            <div className="min-w-0">
              <h1 className="font-[family-name:var(--font-display)] text-[1.35rem] font-bold leading-tight tracking-tight sm:text-3xl">
                {title}
              </h1>
              {subtitle && (
                <p className="mt-1 text-sm leading-relaxed text-muted sm:mt-1.5">
                  {subtitle}
                </p>
              )}
            </div>
            {headerAction ? (
              <div className="shrink-0">{headerAction}</div>
            ) : null}
          </div>
          <div className="mt-4 min-w-0 sm:mt-6">{children}</div>
        </main>
      </div>

      {leaveConfirmOpen && (
        <div
          className="fixed inset-0 z-50 flex items-end justify-center bg-black/50 p-4 sm:items-center"
          role="dialog"
          aria-modal="true"
          aria-labelledby="nav-leave-title"
        >
          <div className="w-full max-w-md rounded-lg border border-line bg-surface p-5 shadow-xl">
            <h2
              id="nav-leave-title"
              className="font-[family-name:var(--font-display)] text-lg font-bold text-ink"
            >
              ¿Salir sin enviar el WhatsApp?
            </h2>
            <p className="mt-2 text-sm leading-relaxed text-muted">
              Aún no has enviado el aviso al cliente. Si sales ahora, el borrador
              se queda en esta orden.
            </p>
            <div className="mt-5 flex flex-col gap-2 sm:flex-row-reverse">
              <button
                type="button"
                onClick={confirmLeave}
                className="btn-brand tap-target inline-flex items-center justify-center rounded-md px-4 py-2.5 text-sm font-semibold"
              >
                Sí, salir
              </button>
              <button
                type="button"
                onClick={() => {
                  setLeaveConfirmOpen(false);
                  setPendingHref(null);
                }}
                className="tap-target inline-flex items-center justify-center rounded-md border border-line bg-surface px-4 py-2.5 text-sm font-semibold text-ink hover:bg-chip"
              >
                Quedarme
              </button>
            </div>
          </div>
        </div>
      )}

      {logoutConfirmOpen && (
        <div
          className="fixed inset-0 z-50 flex items-end justify-center bg-black/50 p-4 sm:items-center"
          role="dialog"
          aria-modal="true"
          aria-labelledby="logout-title"
        >
          <div className="w-full max-w-md rounded-lg border border-line bg-surface p-5 shadow-xl">
            <h2
              id="logout-title"
              className="font-[family-name:var(--font-display)] text-lg font-bold text-ink"
            >
              ¿Cerrar sesión?
            </h2>
            <p className="mt-2 text-sm leading-relaxed text-muted">
              Tendrás que volver a escribir el correo y la contraseña.
            </p>
            <div className="mt-5 flex flex-col gap-2 sm:flex-row-reverse">
              <button
                type="button"
                onClick={doLogout}
                className="btn-brand tap-target inline-flex items-center justify-center rounded-md px-4 py-2.5 text-sm font-semibold"
              >
                Sí, cerrar sesión
              </button>
              <button
                type="button"
                onClick={() => setLogoutConfirmOpen(false)}
                className="tap-target inline-flex items-center justify-center rounded-md border border-line bg-surface px-4 py-2.5 text-sm font-semibold text-ink hover:bg-chip"
              >
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}
    </LeaveGuardContext.Provider>
  );
}
