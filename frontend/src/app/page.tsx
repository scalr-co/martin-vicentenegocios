import Link from "next/link";
import { BrandMark } from "@/components/ui";

export default function HomePage() {
  return (
    <div className="flex min-h-full flex-col bg-background text-ink">
      <header className="absolute inset-x-0 top-0 z-20">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-5 md:px-8">
          <BrandMark light className="text-xl md:text-2xl" />
          <nav className="flex items-center gap-3">
            <Link
              href="/login"
              className="hidden text-sm text-white/80 transition hover:text-white sm:inline"
            >
              Ingresar
            </Link>
            <Link
              href="/login"
              className="rounded-md bg-brand px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-dark"
            >
              Ver demo
            </Link>
          </nav>
        </div>
      </header>

      <section className="relative min-h-[100svh] overflow-hidden">
        <div
          className="absolute inset-0 scale-105 bg-cover bg-center transition-transform duration-[8s] ease-out"
          style={{
            backgroundImage:
              "linear-gradient(105deg, rgba(28,25,23,0.94) 0%, rgba(28,25,23,0.75) 50%, rgba(28,25,23,0.4) 100%), url('https://images.unsplash.com/photo-1486262715619-67b85e0b08d3?auto=format&fit=crop&w=2000&q=80')",
          }}
        />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,rgba(232,93,4,0.28),transparent_55%)]" />

        <div className="relative z-10 mx-auto flex min-h-[100svh] max-w-6xl flex-col justify-end px-5 pb-16 pt-28 md:justify-center md:px-8 md:pb-24">
          <div className="max-w-2xl">
            <p className="animate-rise mb-4 font-[family-name:var(--font-display)] text-sm font-semibold uppercase tracking-[0.22em] text-brand">
              TallerTrack
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
                Probar el panel
              </Link>
              <a
                href="https://wa.me/56900000000?text=Hola%2C%20quiero%20saber%20de%20TallerTrack"
                className="tap-target inline-flex items-center justify-center rounded-md border border-white/30 bg-white/5 px-6 py-3.5 text-sm font-semibold text-white backdrop-blur transition hover:bg-white/10"
              >
                Hablar por WhatsApp
              </a>
            </div>
          </div>
        </div>
      </section>

      <section className="border-t border-line bg-surface px-5 py-20 md:px-8">
        <div className="mx-auto max-w-6xl">
          <h2 className="font-[family-name:var(--font-display)] text-3xl font-bold tracking-tight text-ink md:text-4xl">
            Hecho para el caos real del taller
          </h2>
          <p className="mt-3 max-w-xl text-muted">
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
                className="border-t-2 border-brand pt-5"
                style={{ animationDelay: `${i * 80}ms` }}
              >
                <h3 className="font-[family-name:var(--font-display)] text-xl font-semibold text-ink">
                  {item.title}
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-muted">
                  {item.text}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="bg-background px-5 py-16 md:px-8">
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
                className="rounded-lg border border-line bg-surface p-4"
              >
                <p className="font-[family-name:var(--font-display)] text-sm font-bold text-brand">
                  {String(index + 1).padStart(2, "0")}
                </p>
                <p className="mt-2 text-sm leading-relaxed text-ink">{step}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <section className="bg-steel px-5 py-20 text-white md:px-8">
        <div className="mx-auto flex max-w-6xl flex-col gap-8 md:flex-row md:items-end md:justify-between">
          <div className="max-w-xl">
            <h2 className="font-[family-name:var(--font-display)] text-3xl font-bold tracking-tight md:text-4xl">
              Setup desde $150.000
              <span className="block text-brand">+ $29.990 al mes</span>
            </h2>
            <p className="mt-4 text-white/70">
              Precio de lanzamiento para talleres en Chile. Te dejamos andando y
              te acompañamos los primeros días.
            </p>
          </div>
          <Link
            href="/login"
            className="inline-flex items-center justify-center rounded-md bg-brand px-6 py-3.5 text-sm font-semibold text-white transition hover:bg-brand-dark"
          >
            Ver cómo se ve
          </Link>
        </div>
      </section>

      <footer className="border-t border-line bg-background px-5 py-8 md:px-8">
        <div className="mx-auto flex max-w-6xl flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <BrandMark />
            <p className="mt-2 text-sm text-muted">
              Chillán · Temuco · Hecho para talleres locales
            </p>
          </div>
          <p className="text-xs leading-relaxed text-muted sm:text-right">
            © {new Date().getFullYear()} TallerTrack
            <br />
            Un producto de Martin Web Studio &amp; Solve
          </p>
        </div>
      </footer>
    </div>
  );
}
