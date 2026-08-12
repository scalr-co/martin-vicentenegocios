"use client";

import Link from "next/link";
import { BrandMark } from "@/components/ui";

const PLAN_BASICO = [
  "Órdenes de trabajo ilimitadas",
  "Estados claros (incluye espera de aprobación y repuesto)",
  "Historial por patente",
  "Clientes y vehículos del taller",
  "Aviso al cliente por WhatsApp (link listo)",
  "1 cuenta dueño + hasta 3 mecánicos",
  "El taller crea las cuentas de sus mecánicos",
  "Soporte por WhatsApp",
  "Setup e acompañamiento inicial",
];

/** Extra = todo lo del Básico + más valor (mecánicos sin tope y extras). */
const PLAN_EXTRA = [
  "Órdenes de trabajo ilimitadas",
  "Estados claros (incluye espera de aprobación y repuesto)",
  "Historial por patente",
  "Clientes y vehículos del taller",
  "Aviso al cliente por WhatsApp (link listo)",
  "1 cuenta dueño + mecánicos ilimitados",
  "El taller crea las cuentas de sus mecánicos",
  "Soporte prioritario por WhatsApp",
  "Setup e acompañamiento inicial prioritario",
  "Plantillas de aviso personalizables al taller",
  "Resumen semanal del taller (cuando esté listo)",
  "Exportar clientes e historial (CSV, cuando esté listo)",
];

function PlanFeature({ label }: { label: string }) {
  return (
    <li className="flex items-center gap-3 px-5 py-3.5">
      <span className="min-w-0 flex-1 text-sm font-medium leading-snug text-stone-100">
        {label}
      </span>
      <span
        className="shrink-0 text-[#ea580c]"
        aria-label="Incluido"
        title="Incluido"
      >
        <TicketCheck />
      </span>
    </li>
  );
}

function TicketCheck() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path
        d="M5 12.5 9.5 17 19 7.5"
        stroke="currentColor"
        strokeWidth="2.4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export default function HomePage() {
  return (
    <div className="flex min-h-dvh flex-col">
      {/* Hero: el fondo oscuro/imagen llega hasta el borde superior (sin franja) */}
      <section
        className="relative isolate min-h-svh overflow-hidden"
        style={{ backgroundColor: "#1c1917" }}
      >
        <div
          aria-hidden
          className="absolute inset-0 bg-cover bg-center"
          style={{
            backgroundImage:
              "linear-gradient(105deg, rgba(28,25,23,0.94) 0%, rgba(28,25,23,0.75) 50%, rgba(28,25,23,0.4) 100%), url('https://images.unsplash.com/photo-1486262715619-67b85e0b08d3?auto=format&fit=crop&w=2000&q=80')",
          }}
        />
        <div
          aria-hidden
          className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,rgba(232,93,4,0.28),transparent_55%)]"
        />

        <header className="absolute inset-x-0 top-0 z-20">
          <div className="mx-auto flex max-w-6xl items-center justify-between gap-3 px-5 pb-5 pt-[max(1.25rem,env(safe-area-inset-top))] md:px-8">
            <BrandMark light className="text-xl md:text-2xl" />
            <nav className="flex items-center gap-2 sm:gap-3">
              <a
                href="#precios"
                className="hidden rounded-md px-3 py-2 text-sm font-medium text-white/80 transition hover:text-white sm:inline"
              >
                Precios
              </a>
              <Link
                href="/login"
                className="rounded-md bg-brand px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-dark"
              >
                Ingresar
              </Link>
            </nav>
          </div>
        </header>

        <div className="relative z-10 mx-auto flex min-h-svh max-w-6xl flex-col justify-end px-5 pb-16 pt-28 md:justify-center md:px-8 md:pb-24">
          <div className="max-w-2xl">
            <p className="animate-rise mb-4 font-[family-name:var(--font-display)] text-sm font-semibold uppercase tracking-[0.22em] text-brand">
              Motor Ping
            </p>
            <h1 className="animate-rise-delay font-[family-name:var(--font-display)] text-4xl font-bold leading-[1.05] tracking-tight text-white sm:text-5xl md:text-6xl">
              El cliente sabe en qué va.
              <span className="block text-white/85">Sin llamarte veinte veces.</span>
            </h1>
            <p className="animate-fade mt-5 max-w-lg text-base leading-relaxed text-white/75 md:text-lg">
              Órdenes de trabajo para talleres: estados claros, historial por
              patente y aviso por WhatsApp cuando el trabajo avanza o se queda
              esperando aprobación o repuesto.
            </p>
            <div className="animate-fade mt-8 flex w-full flex-col gap-3 sm:w-auto sm:flex-row">
              <Link
                href="/login"
                className="tap-target inline-flex items-center justify-center rounded-md bg-brand px-6 py-3.5 text-sm font-semibold text-white transition hover:bg-brand-dark"
              >
                Ingresar
              </Link>
              <a
                href="https://wa.me/56981875498?text=Hola%2C%20quiero%20saber%20de%20Motor%20Ping"
                className="tap-target inline-flex items-center justify-center rounded-md border border-white/30 bg-white/5 px-6 py-3.5 text-sm font-semibold text-white backdrop-blur transition hover:bg-white/10"
              >
                Hablar por WhatsApp
              </a>
            </div>
          </div>
        </div>
      </section>

      <section className="border-t border-white/10 bg-[#1c1917] px-5 py-20 text-white md:px-8">
        <div className="mx-auto max-w-6xl">
          <h2 className="font-[family-name:var(--font-display)] text-3xl font-bold tracking-tight md:text-4xl">
            Hecho para el caos real del taller
          </h2>
          <p className="mt-3 max-w-xl text-white/70">
            No es otra agenda. Es el seguimiento del auto mientras está en tu
            piso — incluyendo cuando está quieto esperando al cliente o a una
            pieza.
          </p>

          <div className="mt-12 grid gap-10 md:grid-cols-3">
            {[
              {
                title: "Estados que importan",
                text: "Incluye esperando aprobación y esperando repuesto: ahí es donde más llaman.",
              },
              {
                title: "Historial por patente",
                text: "Ves si ese auto ya vino por frenos. Eso hace que no se cambien de sistema.",
              },
              {
                title: "Aviso al cliente",
                text: "Hoy: botón WhatsApp con el mensaje listo. Después: envío automático sin cambiar tu pantalla.",
              },
            ].map((item, i) => (
              <div
                key={item.title}
                className="border-t-2 border-[#c2410c] pt-5"
                style={{ animationDelay: `${i * 80}ms` }}
              >
                <h3 className="font-[family-name:var(--font-display)] text-xl font-semibold text-white">
                  {item.title}
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-white/65">
                  {item.text}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="bg-[#141210] px-5 py-16 text-white md:px-8">
        <div className="mx-auto max-w-6xl">
          <h2 className="font-[family-name:var(--font-display)] text-2xl font-bold tracking-tight md:text-3xl">
            Flujo del día
          </h2>
          <ol className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[
              "Entras el trabajo con patente y foto",
              "Marcas el estado real (también si espera)",
              "Aviso listo para WhatsApp al cliente",
              "Entregas con historial guardado",
            ].map((step, index) => (
              <li
                key={step}
                className="rounded-lg border border-white/15 bg-[#292524] p-4"
              >
                <p className="font-[family-name:var(--font-display)] text-sm font-bold text-[#ea580c]">
                  {String(index + 1).padStart(2, "0")}
                </p>
                <p className="mt-2 text-sm leading-relaxed text-white/85">
                  {step}
                </p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <section
        id="precios"
        className="border-t border-white/10 bg-[#1c1917] px-5 py-20 md:px-8"
      >
        <div className="mx-auto max-w-6xl">
          <h2 className="font-[family-name:var(--font-display)] text-3xl font-bold tracking-tight text-white md:text-4xl">
            Planes para tu taller
          </h2>
          <p className="mt-3 max-w-2xl text-sm leading-relaxed text-white/70 md:text-base">
            Nosotros te damos de alta el taller. Tú creas las cuentas de tus
            mecánicos. Elige según cuántas personas usan el sistema.
          </p>

          <div className="mt-12 grid items-start gap-6 lg:grid-cols-2">
            {/* Básico */}
            <article className="overflow-hidden rounded-xl border border-white/15 bg-[#292524]">
              <div className="border-b border-white/10 px-6 py-5">
                <p className="font-[family-name:var(--font-display)] text-xl font-bold uppercase tracking-wide text-white">
                  Básico
                </p>
                <p className="mt-1 text-sm text-white/65">
                  Ideal para talleres chicos con poco equipo
                </p>
                <p className="mt-4 font-[family-name:var(--font-display)] text-3xl font-bold text-white">
                  $24.990
                  <span className="text-base font-semibold text-white/65">
                    {" "}
                    / mes
                  </span>
                </p>
                <p className="mt-1 text-xs text-white/55">
                  + setup $120.000 (una vez)
                </p>
              </div>
              <ul className="divide-y divide-white/10">
                {PLAN_BASICO.map((item) => (
                  <PlanFeature key={item} label={item} />
                ))}
              </ul>
              <div className="px-6 pb-6 pt-2">
                <a
                  href="https://wa.me/56981875498?text=Hola%2C%20quiero%20el%20plan%20B%C3%A1sico%20de%20Motor%20Ping"
                  className="tap-target inline-flex w-full items-center justify-center rounded-md border border-white/25 bg-transparent px-4 py-3 text-sm font-semibold text-white transition hover:bg-white/10"
                >
                  Quiero el Básico
                </a>
              </div>
            </article>

            {/* Extra — se nota más: borde y cabecera naranja de marca */}
            <article className="overflow-hidden rounded-xl border border-[#c2410c]/60 bg-[#292524] shadow-[0_0_0_1px_rgba(194,65,12,0.25)]">
              <div className="border-b border-[#c2410c]/40 bg-[#c2410c] px-6 py-5 text-white">
                <p className="font-[family-name:var(--font-display)] text-xl font-bold uppercase tracking-wide">
                  Extra
                </p>
                <p className="mt-1 text-sm text-white/95">
                  Todo el Básico, sin tope de mecánicos y con más potencia
                </p>
                <p className="mt-4 font-[family-name:var(--font-display)] text-3xl font-bold">
                  $44.990
                  <span className="text-base font-semibold text-white/90">
                    {" "}
                    / mes
                  </span>
                </p>
                <p className="mt-1 text-xs text-white/85">
                  + setup $150.000 (una vez)
                </p>
              </div>
              <ul className="divide-y divide-white/10">
                {PLAN_EXTRA.map((item) => (
                  <PlanFeature key={item} label={item} />
                ))}
              </ul>
              <div className="px-6 pb-6 pt-2">
                <a
                  href="https://wa.me/56981875498?text=Hola%2C%20quiero%20el%20plan%20Extra%20de%20Motor%20Ping"
                  className="tap-target inline-flex w-full items-center justify-center rounded-md bg-[#c2410c] px-4 py-3 text-sm font-semibold text-white transition hover:bg-[#9a3412]"
                >
                  Quiero el Extra
                </a>
              </div>
            </article>
          </div>

          <p className="mt-8 text-center text-sm text-white/55">
            Precios de lanzamiento en Chile · IVA no incluido · Se pueden ajustar
            al cerrar contigo
          </p>
        </div>
      </section>

      <footer className="border-t border-white/10 bg-[#141210] px-5 pb-[max(2rem,env(safe-area-inset-bottom))] pt-8 text-white md:px-8">
        <div className="mx-auto flex max-w-6xl flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <BrandMark light />
            <p className="mt-2 text-sm text-white/60">
              Chillán · Temuco · Hecho para talleres locales
            </p>
          </div>
          <p className="text-xs leading-relaxed text-white/45 sm:text-right">
            © {new Date().getFullYear()} Motor Ping
            <br />
            Un producto de Martin Web Studio &amp; Solve
          </p>
        </div>
      </footer>
    </div>
  );
}
