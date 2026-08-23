import Link from "next/link";
import { BrandMark } from "@/components/ui";

export function LegalShell({
  title,
  updated,
  children,
}: {
  title: string;
  updated: string;
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-dvh bg-[#1c1917] text-white">
      <header className="border-b border-white/10">
        <div className="mx-auto flex max-w-3xl items-center justify-between gap-4 px-5 py-4 md:px-8">
          <BrandMark light className="text-lg" />
          <Link
            href="/"
            className="tap-target inline-flex items-center text-sm text-white/70 hover:text-white"
          >
            ← Volver
          </Link>
        </div>
      </header>

      <main className="mx-auto max-w-3xl px-5 py-10 md:px-8 md:py-14">
        <p
          className="text-xs font-semibold uppercase tracking-[0.18em]"
          style={{ color: "#e0a45a" }}
        >
          Motor Ping
        </p>
        <h1 className="mt-3 font-[family-name:var(--font-display)] text-3xl font-bold tracking-tight md:text-4xl">
          {title}
        </h1>
        <p className="mt-2 text-sm text-white/55">Última actualización: {updated}</p>

        <div className="legal-prose mt-10 space-y-8 text-sm leading-relaxed text-white/75">
          {children}
        </div>

        <p className="mt-12 border-t border-white/10 pt-6 text-xs text-white/45">
          Este documento es una versión operativa alineada a la{" "}
          <strong className="font-medium text-white/60">
            Ley N° 21.719
          </strong>{" "}
          (protección de datos personales en Chile), con vigencia plena desde el{" "}
          <strong className="font-medium text-white/60">
            1 de diciembre de 2026
          </strong>
          . No reemplaza asesoría legal: si tu taller necesita cláusulas
          específicas, consúltanos o a un abogado.
        </p>
      </main>
    </div>
  );
}

export function LegalH2({ children }: { children: React.ReactNode }) {
  return (
    <h2 className="font-[family-name:var(--font-display)] text-lg font-semibold text-white">
      {children}
    </h2>
  );
}

export function LegalList({ items }: { items: string[] }) {
  return (
    <ul className="mt-3 list-disc space-y-2 pl-5 marker:text-[#e0a45a]">
      {items.map((item) => (
        <li key={item}>{item}</li>
      ))}
    </ul>
  );
}
