import type { Metadata } from "next";
import Link from "next/link";
import { LegalH2, LegalList, LegalShell } from "@/components/legal-shell";

export const metadata: Metadata = {
  title: "Términos de uso — Motor Ping",
  description:
    "Condiciones de uso del servicio Motor Ping para talleres en Chile.",
};

export default function TerminosPage() {
  return (
    <LegalShell title="Términos de uso" updated="11 de agosto de 2026">
      <section>
        <p>
          Estos términos regulan el acceso y uso de Motor Ping, el software de
          órdenes de trabajo y avisos a clientes para talleres. Al crear una
          cuenta, ingresar al panel o contratar un plan, aceptas estas
          condiciones. Si no estás de acuerdo, no uses el servicio.
        </p>
        <p className="mt-3">
          El tratamiento de datos personales se detalla en la{" "}
          <Link
            href="/privacidad"
            className="underline decoration-[#c9bfb0]/60 underline-offset-2 hover:text-white"
          >
            Política de privacidad
          </Link>
          , alineada a la Ley N° 21.719 de Chile (vigencia plena desde el 1 de
          diciembre de 2026).
        </p>
      </section>

      <section>
        <LegalH2>1. El servicio</LegalH2>
        <p className="mt-3">
          Motor Ping permite registrar órdenes, estados, clientes, vehículos y
          preparar avisos por WhatsApp (modo enlace wa.me). Las cuentas de
          taller las da de alta el equipo de Motor Ping; el taller puede crear
          cuentas de mecánicos según su plan (Básico: hasta 3; Extra: sin tope,
          según lo publicado).
        </p>
      </section>

      <section>
        <LegalH2>2. Cuentas y seguridad</LegalH2>
        <LegalList
          items={[
            "Debes entregar información veraz al registrarte o al dar de alta mecánicos",
            "Eres responsable de custodiar tus credenciales y de la actividad hecha con tu cuenta",
            "Avisa de inmediato si sospechas acceso no autorizado",
            "No compartas accesos de admin de plataforma; esos son solo para el equipo Motor Ping",
          ]}
        />
      </section>

      <section>
        <LegalH2>3. Uso permitido</LegalH2>
        <p className="mt-3">Te comprometes a usar el servicio solo para:</p>
        <LegalList
          items={[
            "Gestionar trabajos reales de tu taller",
            "Comunicarte con tus clientes de forma lícita y respetuosa",
            "Cumplir la normativa aplicable, incluida la protección de datos de tus clientes",
          ]}
        />
        <p className="mt-3">Queda prohibido, entre otros:</p>
        <LegalList
          items={[
            "Usar el sistema para spam, fraude o acoso",
            "Intentar vulnerar seguridad, copiar o revender el software sin autorización",
            "Cargar datos de terceros sin base legal o consentimiento cuando corresponda",
            "Interferir con el servicio de otros talleres",
          ]}
        />
      </section>

      <section>
        <LegalH2>4. Datos de tus clientes</LegalH2>
        <p className="mt-3">
          Como taller, eres responsable de los datos personales de tus clientes
          que ingresas (nombre, teléfono, RUT, historial, etc.). Debes contar
          con una base de licitud válida bajo la Ley 21.719 e informarles cuando
          corresponda. Motor Ping trata esos datos para prestarte el servicio,
          según la Política de privacidad y el contrato.
        </p>
      </section>

      <section>
        <LegalH2>5. Planes, precios y pago</LegalH2>
        <p className="mt-3">
          Los planes (Básico / Extra), precios de setup y mensualidad se
          publican en el sitio y pueden actualizarse. Los cobros se acuerdan al
          contratar. El no pago puede implicar suspensión o término del acceso,
          previo aviso razonable cuando sea posible.
        </p>
      </section>

      <section>
        <LegalH2>6. Disponibilidad y cambios</LegalH2>
        <p className="mt-3">
          Buscamos un servicio estable, pero no garantizamos disponibilidad
          ininterrumpida (mantenimientos, fallas de terceros, fuerza mayor).
          Podemos mejorar, modificar o discontinuar funciones; si el cambio es
          material, avisaremos por medios razonables.
        </p>
      </section>

      <section>
        <LegalH2>7. Propiedad intelectual</LegalH2>
        <p className="mt-3">
          El software, marca Motor Ping, diseños y contenidos de la plataforma
          son de Martin Web Studio &amp; Solve o de sus licenciantes. Se te
          otorga una licencia limitada, no exclusiva y revocable para usar el
          servicio mientras tu cuenta esté activa. No adquieres propiedad sobre
          el código ni la marca.
        </p>
      </section>

      <section>
        <LegalH2>8. Limitación de responsabilidad</LegalH2>
        <p className="mt-3">
          En la máxima medida permitida por la ley chilena, no respondemos por
          daños indirectos, lucro cesante o pérdida de datos causada por
          terceros (incluido WhatsApp), uso indebido de la cuenta o fuerza
          mayor. Nuestra responsabilidad agregada, cuando proceda, se limita a
          lo efectivamente pagado por el taller en los tres meses anteriores al
          hecho, salvo dolo o culpa grave.
        </p>
      </section>

      <section>
        <LegalH2>9. Suspensión y término</LegalH2>
        <p className="mt-3">
          Podemos suspender o cerrar cuentas ante incumplimiento grave de estos
          términos, riesgo de seguridad o requerimiento legal. Tú puedes dejar
          de usar el servicio y solicitar la baja; gestionaremos la
          conservación/eliminación de datos según la Política de privacidad y la
          Ley 21.719.
        </p>
      </section>

      <section>
        <LegalH2>10. Ley aplicable</LegalH2>
        <p className="mt-3">
          Estos términos se rigen por las leyes de la República de Chile. Cualquier
          controversia se someterá a los tribunales competentes de Chile, sin
          perjuicio de derechos irrenunciables del consumidor cuando apliquen.
        </p>
      </section>

      <section>
        <LegalH2>11. Contacto</LegalH2>
        <p className="mt-3">
          Dudas sobre el servicio o estos términos: WhatsApp{" "}
          <strong className="text-white/90">+56 9 8187 5498</strong> (Chillán ·
          Temuco).
        </p>
      </section>
    </LegalShell>
  );
}
