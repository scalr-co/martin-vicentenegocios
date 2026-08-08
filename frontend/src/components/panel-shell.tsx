"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { BrandMark } from "@/components/ui";
import { clearSession, getWorkshopName } from "@/lib/auth";

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
          ? "bg-stone-900 text-white"
          : "text-muted hover:bg-stone-100 hover:text-ink"
      }`}
    >
      {label}
    </Link>
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
  const workshop = getWorkshopName();

  return (
    <div className="min-h-full bg-background text-ink">
      <header className="sticky top-0 z-30 border-b border-line bg-surface/95 backdrop-blur">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-4 px-4 py-3">
          <div className="flex items-center gap-6">
            <BrandMark className="text-lg" />
            <nav className="hidden items-center gap-1 sm:flex">
              {links.map((link) => (
                <NavLink key={link.href} {...link} />
              ))}
            </nav>
          </div>
          <div className="flex items-center gap-3">
            <div className="hidden text-right sm:block">
              <p className="text-xs font-medium text-ink">{workshop}</p>
              <p className="text-[11px] text-muted">Modo WhatsApp: link</p>
            </div>
            <button
              type="button"
              onClick={() => {
                clearSession();
                router.replace("/login");
              }}
              className="rounded-md px-2 py-1 text-xs text-muted hover:bg-stone-100 hover:text-ink"
            >
              Salir
            </button>
          </div>
        </div>
        <nav className="flex gap-1 overflow-x-auto border-t border-line px-4 py-2 sm:hidden">
          {links.map((link) => (
            <NavLink key={link.href} {...link} />
          ))}
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
