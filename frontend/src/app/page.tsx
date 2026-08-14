"use client";

import Link from "next/link";
import { BrandMark } from "@/components/ui";
import { PLAN_BASICO_FEATURES, PLAN_PLUS_FEATURES } from "@/lib/plans";

/**
 * Dirección visual: piedra de taller + cobre/ámbar (luz de piso, metal).
 * Más contraste que el beige anterior; sigue profesional, no neon.
 */
const ACCENT = "#e0a45a";
const ACCENT_SOFT = "#f0c48a";
const CTA = "#f5f0e8";
const CTA_TEXT = "#1c1917";
const INK = "#12100e";
const SURFACE = "#1a1714";
const SURFACE_RAISED = "#26211c";

function PlanFeature({
  label,
  checkColor = ACCENT,
}: {
  label: string;
  checkColor?: string;
}) {
  return (
    <li className="flex items-center gap-3 px-5 py-3.5">
      <span className="min-w-0 flex-1 text-sm font-medium leading-snug text-stone-100">
        {label}
      </span>
      <span
        className="shrink-0"
        style={{ color: checkColor }}
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

/** Baja suave hasta un ancla (más pausado que el smooth nativo). */
function scrollToId(id: string, e?: React.MouseEvent) {
  e?.preventDefault();
  const el = document.getElementById(id);
  if (!el) return;

  const reduceMotion = window.matchMedia(
    "(prefers-reduced-motion: reduce)",
  ).matches;
  if (reduceMotion) {
    el.scrollIntoView();
    history.replaceState(null, "", `#${id}`);
    return;
  }

  const start = window.scrollY;
  const end = el.getBoundingClientRect().top + window.scrollY;
  const distance = end - start;
  const duration = Math.min(1400, Math.max(700, Math.abs(distance) * 0.55));
  let startTime: number | null = null;

  function step(now: number) {
    if (startTime === null) startTime = now;
    const t = Math.min((now - startTime) / duration, 1);
    const eased =
      t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
    window.scrollTo(0, start + distance * eased);
    if (t < 1) requestAnimationFrame(step);
    else history.replaceState(null, "", `#${id}`);
  }

  requestAnimationFrame(step);
}

export default function HomePage() {
  return (
    <div className="flex min-h-dvh flex-col" style={{ backgroundColor: INK }}>
      <section
        className="relative isolate min-h-svh overflow-hidden"
        style={{ backgroundColor: INK }}
      >
        <div
          aria-hidden
          className="absolute inset-0 bg-cover bg-center"
          style={{
            backgroundImage:
              "linear-gradient(105deg, rgba(18,16,14,0.94) 0%, rgba(18,16,14,0.72) 48%, rgba(18,16,14,0.35) 100%), url('https://images.unsplash.com/photo-1486262715619-67b85e0b08d3?auto=format&fit=crop&w=2000&q=80')",
          }}
        />
        <div
          aria-hidden
          className="absolute inset-0"
          style={{
            background:
              "radial-gradient(ellipse at top right, rgba(224,164,90,0.28), transparent 52%)",
          }}
        />

        <header className="absolute inset-x-0 top-0 z-20">
          <div className="mx-auto flex max-w-6xl items-center justify-between gap-3 px-5 pb-5 pt-[max(1.25rem,env(safe-area-inset-top))] md:px-8">
            <BrandMark light className="text-xl md:text-2xl" />
            <nav className="flex items-center gap-2 sm:gap-3">
              <a
                href="#precios"
                onClick={(e) => scrollToId("precios", e)}
                className="tap-target inline-flex items-center rounded-md px-3 py-2 text-sm font-medium text-white/80 transition hover:text-white"
              >
                Precios
              </a>
              <Link
                href="/login"
                className="tap-target inline-flex items-center rounded-md px-4 py-2 text-sm font-semibold transition hover:brightness-110"
                style={{ backgroundColor: CTA, color: CTA_TEXT }}
              >
                Ingresar
              </Link>
            </nav>
          </div>
        </header>

        <div className="relative z-10 mx-auto flex min-h-svh max-w-6xl flex-col justify-end px-5 pb-16 pt-28 md:justify-center md:px-8 md:pb-24">
          <div className="max-w-2xl">
            <p
              className="animate-rise mb-4 font-[family-name:var(--font-display)] text-sm font-semibold uppercase tracking-[0.22em]"
              style={{ color: ACCENT_SOFT }}
            >
              Motor Ping
            </p>
            <h1 className="animate-rise-delay font-[family-name:var(--font-display)] text-4xl font-bold leading-[1.05] tracking-tight text-white sm:text-5xl md:text-6xl">
              Menos llamadas.
              <span className="block text-white/90">
                Más control del taller
              </span>
            </h1>
            <p className="animate-fade mt-5 max-w-lg text-base leading-relaxed text-white/78 md:text-lg">
              Órdenes de trabajo para talleres: estados claros, historial por
              patente y aviso por WhatsApp cuando el trabajo avanza o se queda
              esperando aprobación o repuesto.
            </p>
            <div className="animate-fade mt-8 flex w-full flex-col gap-3 sm:w-auto sm:flex-row">
              <Link
                href="/login"
                className="tap-target inline-flex items-center justify-center rounded-md px-6 py-3.5 text-sm font-semibold transition hover:brightness-110"
                style={{ backgroundColor: CTA, color: CTA_TEXT }}
              >
                Ingresar
              </Link>
              <a
                href="https://wa.me/56981875498?text=Hola%2C%20quiero%20saber%20de%20Motor%20Ping"
                className="tap-target inline-flex items-center justify-center rounded-md border border-white/35 bg-white/8 px-6 py-3.5 text-sm font-semibold text-white backdrop-blur transition hover:bg-white/14"
              >
                Hablar por WhatsApp
              </a>
            </div>
          </div>
        </div>
      </section>

      <section
        className="border-t border-white/10 px-5 py-20 text-white md:px-8"
        style={{
          background:
            `linear-gradient(180deg, ${SURFACE} 0%, ${INK} 100%)`,
        }}
      >
        <div className="mx-auto max-w-6xl">
          <h2 className="font-[family-name:var(--font-display)] text-3xl font-bold tracking-tight md:text-4xl">
            Hecho para el caos real del taller
          </h2>
          <p className="mt-3 max-w-xl text-white/72">
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
                className="border-t-[3px] pt-5"
                style={{
                  borderColor: ACCENT,
                  animationDelay: `${i * 80}ms`,
                }}
              >
                <h3 className="font-[family-name:var(--font-display)] text-xl font-semibold text-white">
                  {item.title}
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-white/68">
                  {item.text}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section
        className="px-5 py-16 text-white md:px-8"
        style={{ backgroundColor: INK }}
      >
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
                className="rounded-lg border border-white/12 p-4"
                style={{ backgroundColor: SURFACE_RAISED }}
              >
                <p
                  className="font-[family-name:var(--font-display)] text-sm font-bold"
                  style={{ color: ACCENT }}
                >
                  {String(index + 1).padStart(2, "0")}
                </p>
                <p className="mt-2 text-sm leading-relaxed text-white/88">
                  {step}
                </p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <section
        id="precios"
        className="relative overflow-hidden border-t border-white/10 px-5 py-20 md:px-8"
        style={{
          background:
            `radial-gradient(ellipse at 70% 0%, rgba(224,164,90,0.16), transparent 55%), linear-gradient(180deg, ${SURFACE} 0%, ${INK} 100%)`,
        }}
      >
        <div className="relative mx-auto max-w-6xl">
          <h2 className="font-[family-name:var(--font-display)] text-3xl font-bold tracking-tight text-white md:text-4xl">
            Planes para tu taller
          </h2>
          <p className="mt-3 max-w-2xl text-sm leading-relaxed text-white/72 md:text-base">
            Nosotros te damos de alta el taller. Tú creas las cuentas de tus
            mecánicos. Elige según cuántas personas usan el sistema.
          </p>

          <div className="mt-12 grid items-stretch gap-6 lg:grid-cols-2 lg:gap-8">
            {/* Básico: quieto, profesional */}
            <article
              className="flex flex-col overflow-hidden rounded-xl border border-white/14"
              style={{ backgroundColor: SURFACE_RAISED }}
            >
              <div className="border-b border-white/10 px-6 py-5">
                <p className="font-[family-name:var(--font-display)] text-xl font-bold uppercase tracking-wide text-white/90">
                  Básico
                </p>
                <p className="mt-1 text-sm text-white/60">
                  Ideal para talleres chicos con poco equipo
                </p>
                <p className="mt-4 font-[family-name:var(--font-display)] text-3xl font-bold text-white">
                  $29.990
                  <span className="text-base font-semibold text-white/60">
                    {" "}
                    / mes
                  </span>
                </p>
                <p className="mt-1 text-xs text-white/50">
                  + setup $120.000 (una vez)
                </p>
              </div>
              <ul className="flex-1 divide-y divide-white/10">
                {PLAN_BASICO_FEATURES.map((item) => (
                  <PlanFeature
                    key={item}
                    label={item}
                    checkColor="#a8a29e"
                  />
                ))}
              </ul>
              <div className="px-6 pb-6 pt-2">
                <a
                  href="https://wa.me/56981875498?text=Hola%2C%20quiero%20el%20plan%20B%C3%A1sico%20de%20Motor%20Ping"
                  className="tap-target inline-flex w-full items-center justify-center rounded-md border border-white/28 bg-transparent px-4 py-3 text-sm font-semibold text-white transition hover:bg-white/10"
                >
                  Quiero el Básico
                </a>
              </div>
            </article>

            {/* Plus: acento cobre, claramente destacado */}
            <article
              className="relative flex flex-col overflow-hidden rounded-xl"
              style={{
                backgroundColor: "#2c241c",
                border: `1.5px solid ${ACCENT}`,
                boxShadow:
                  `0 0 0 1px rgba(224,164,90,0.25), 0 18px 50px -20px rgba(224,164,90,0.45)`,
              }}
            >
              <div
                className="absolute inset-x-0 top-0 h-1"
                style={{
                  background: `linear-gradient(90deg, ${ACCENT}, ${ACCENT_SOFT}, ${ACCENT})`,
                }}
              />
              <div
                className="border-b px-6 py-5"
                style={{
                  background:
                    "linear-gradient(160deg, rgba(224,164,90,0.22) 0%, rgba(44,36,28,0.95) 70%)",
                  borderColor: "rgba(224,164,90,0.35)",
                }}
              >
                <div className="flex flex-wrap items-center gap-2">
                  <p
                    className="font-[family-name:var(--font-display)] text-xl font-bold uppercase tracking-wide"
                    style={{ color: ACCENT_SOFT }}
                  >
                    Plus
                  </p>
                  <span
                    className="rounded-md px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wide"
                    style={{
                      backgroundColor: ACCENT,
                      color: CTA_TEXT,
                    }}
                  >
                    Recomendado
                  </span>
                </div>
                <p className="mt-1 text-sm text-white/80">
                  Todo el Básico, sin tope de mecánicos y con más potencia
                </p>
                <p className="mt-4 font-[family-name:var(--font-display)] text-3xl font-bold text-white">
                  $44.990
                  <span className="text-base font-semibold text-white/75">
                    {" "}
                    / mes
                  </span>
                </p>
                <p className="mt-1 text-xs text-white/55">
                  + setup $150.000 (una vez)
                </p>
              </div>
              <ul className="flex-1 divide-y divide-white/10">
                {PLAN_PLUS_FEATURES.map((item) => (
                  <PlanFeature key={item} label={item} checkColor={ACCENT} />
                ))}
              </ul>
              <div className="px-6 pb-6 pt-2">
                <a
                  href="https://wa.me/56981875498?text=Hola%2C%20quiero%20el%20plan%20Plus%20de%20Motor%20Ping"
                  className="tap-target inline-flex w-full items-center justify-center rounded-md px-4 py-3 text-sm font-semibold transition hover:brightness-110"
                  style={{ backgroundColor: ACCENT, color: CTA_TEXT }}
                >
                  Quiero el Plus
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

      <footer
        className="border-t border-white/10 px-5 pb-[max(2rem,env(safe-area-inset-bottom))] pt-8 text-white md:px-8"
        style={{ backgroundColor: "#0c0a09" }}
      >
        <div className="mx-auto flex max-w-6xl flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <BrandMark light />
            <p className="mt-2 text-sm text-white/60">
              Chillán · Temuco · Hecho para talleres locales
            </p>
            <nav className="mt-4 flex flex-wrap gap-x-4 gap-y-2 text-sm">
              <Link
                href="/privacidad"
                className="text-white/70 underline-offset-2 hover:text-white hover:underline"
              >
                Política de privacidad
              </Link>
              <Link
                href="/terminos"
                className="text-white/70 underline-offset-2 hover:text-white hover:underline"
              >
                Términos de uso
              </Link>
            </nav>
          </div>
          <p className="text-xs leading-relaxed text-white/45 sm:text-right">
            © {new Date().getFullYear()} Motor Ping
            <br />
            Un producto de Martin Web Studio &amp; Solve
            <br />
            <span className="mt-1 inline-block text-white/35">
              Privacidad alineada a la Ley 21.719 (Chile)
            </span>
          </p>
        </div>
      </footer>
    </div>
  );
}
