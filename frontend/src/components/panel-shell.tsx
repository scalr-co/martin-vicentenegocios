"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useSyncExternalStore } from "react";
import { clearSession, getWorkshopName, isAdmin } from "@/lib/auth";
import { ThemeToggle } from "@/components/theme-toggle";

const links = [
  { href: "/panel", label: "Hoy", exact: true },
  { href: "/panel/clientes", label: "Clientes", exact: false },
  { href: "/panel/nueva-orden", label: "Nueva orden", exact: false },
];

function NavLink({
  href,
  label,
  exact,
}: {
  href: string;
  label: string;
  exact: boolean;
}) {
  const pathname = usePathname();
  const active = exact ? pathname === href : pathname.startsWith(href);

  return (
    <Link
      href={href}
      className={`tap-target inline-flex items-center rounded-md px-3 py-1.5 text-sm transition ${
        active
          ? "bg-steel text-white"
          : "text-muted hover:bg-stone-100 hover:text-ink dark:hover:bg-stone-800"
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
  children,
}: {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
}) {
  const router = useRouter();
  const workshop = useClientWorkshopName();
  const admin = useClientFlag(() => isAdmin());
  const pathname = usePathname();
  const adminActive = pathname.startsWith("/panel/admin");

  const nav = [
    ...links,
    ...(admin
      ? [{ href: "/panel/admin", label: "Admin", exact: false as const }]
      : []),
  ];

  return (
    <div className="flex min-h-dvh flex-1 flex-col bg-background text-ink">
      <header className="sticky top-0 z-30 border-b border-line bg-surface/95 backdrop-blur">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-4 px-4 py-3">
          <div className="flex min-w-0 items-center gap-6">
            <Link href="/panel" className="min-w-0">
              <span className="block truncate font-[family-name:var(--font-display)] text-lg font-bold tracking-tight text-ink">
                {admin ? "Motor Ping Admin" : workshop}
              </span>
              {!admin && (
                <span className="block text-[10px] font-medium uppercase tracking-[0.14em] text-muted">
                  Motor Ping
                </span>
              )}
            </Link>
            <nav className="hidden items-center gap-1 sm:flex">
              {nav.map((link) => (
                <NavLink key={link.href} {...link} />
              ))}
            </nav>
          </div>
          <div className="flex items-center gap-2 sm:gap-3">
            <ThemeToggle />
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
              onClick={() => {
                clearSession();
                router.replace("/login");
              }}
              className="rounded-md px-2 py-1 text-xs text-muted hover:bg-stone-100 hover:text-ink dark:hover:bg-stone-800"
            >
              Salir
            </button>
          </div>
        </div>
        <nav className="flex gap-1 overflow-x-auto border-t border-line px-4 py-2 sm:hidden">
          {nav.map((link) => (
            <NavLink key={link.href} {...link} />
          ))}
          {admin && (
            <span className="sr-only">
              {adminActive ? "Admin activo" : "Admin"}
            </span>
          )}
        </nav>
      </header>

      <main className="mx-auto max-w-5xl px-4 py-6 pb-24 sm:py-8 sm:pb-10">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div className="min-w-0">
            <h1 className="font-[family-name:var(--font-display)] text-[1.65rem] font-bold leading-tight tracking-tight sm:text-3xl">
              {title}
            </h1>
            {subtitle && (
              <p className="mt-1.5 text-sm leading-relaxed text-muted">
                {subtitle}
              </p>
            )}
          </div>
        </div>
        <div className="mt-5 sm:mt-6">{children}</div>
      </main>
    </div>
  );
}
