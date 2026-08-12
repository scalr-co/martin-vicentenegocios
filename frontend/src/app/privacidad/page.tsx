import type { Metadata } from "next";
import { LegalH2, LegalList, LegalShell } from "@/components/legal-shell";

export const metadata: Metadata = {
  title: "Política de privacidad — Motor Ping",
  description:
    "Cómo Motor Ping trata datos personales conforme a la Ley 21.719 de Chile.",
};

export default function PrivacidadPage() {
  return (
    <LegalShell title="Política de privacidad" updated="11 de agosto de 2026">
      <section>
        <p>
          En Motor Ping (producto de Martin Web Studio y Solve) tratamos datos
          personales para prestar el servicio de órdenes de trabajo y avisos a
          clientes de talleres en Chile. Esta política informa, de forma
          permanente y accesible, quiénes somos, qué datos usamos, para qué, con
          qué base legal y cómo puedes ejercer tus derechos, de acuerdo con la{" "}
          <strong className="text-white/90">Ley N° 21.719</strong> (que modifica
          la Ley N° 19.628) y que entra en vigencia plena el{" "}
          <strong className="text-white/90">1 de diciembre de 2026</strong>.
        </p>
      </section>

      <section>
        <LegalH2>1. Responsable del tratamiento</LegalH2>
        <p className="mt-3">
          El responsable del tratamiento de los datos personales tratados a
          través de esta plataforma es el equipo de Motor Ping (Martin Web
          Studio &amp; Solve), con operaciones en Chillán y Temuco, Chile.
        </p>
        <LegalList
          items={[
            "Contacto para privacidad y derechos: WhatsApp +56 9 8187 5498",
            "Correo de contacto operativo: el que indiquemos al contratar el servicio",
            "Sitio: tallertrack-nine.vercel.app (marca Motor Ping)",
          ]}
        />
        <p className="mt-3">
          Cuando un taller usa Motor Ping, ese taller también puede actuar como
          responsable respecto de los datos de <em>sus</em> clientes (nombre,
          teléfono, RUT, vehículo, historial del trabajo). Nosotros tratamos
          esos datos como encargados/proveedores del servicio, según el contrato
          con el taller.
        </p>
      </section>

      <section>
        <LegalH2>2. Qué datos tratamos</LegalH2>
        <p className="mt-3">Según el uso del servicio, podemos tratar:</p>
        <LegalList
          items={[
            "Datos de cuenta del taller: nombre, correo, teléfono, rol (dueño/mecánico/admin)",
            "Datos de clientes del taller: nombre, WhatsApp/teléfono, RUT u otras notas que el taller registre",
            "Datos de vehículos: patente, marca, modelo",
            "Órdenes de trabajo: título, descripción, estados, fechas estimadas, historial",
            "Avisos: mensajes preparados o enviados por WhatsApp (enlace wa.me) y registro de envío",
            "Datos técnicos mínimos: IP, tipo de dispositivo, registros de acceso/seguridad",
          ]}
        />
        <p className="mt-3">
          No pedimos datos sensibles de salud u otros especiales salvo que el
          taller los escriba voluntariamente en una descripción; pedimos evitar
          esa práctica.
        </p>
      </section>

      <section>
        <LegalH2>3. Finalidades y bases de licitud</LegalH2>
        <p className="mt-3">Tratamos los datos para:</p>
        <LegalList
          items={[
            "Crear y administrar cuentas de talleres y mecánicos (ejecución de contrato / medidas precontractuales)",
            "Gestionar órdenes, estados e historial por patente (ejecución del servicio contratado)",
            "Facilitar el aviso al cliente por WhatsApp mediante enlace listo (interés legítimo del taller y ejecución del servicio; el envío lo confirma el usuario del taller)",
            "Soporte, seguridad, prevención de abuso y mejora del producto (interés legítimo, con evaluación de impacto cuando corresponda)",
            "Cumplir obligaciones legales y requerimientos de autoridad",
            "Facturación y cobranza del plan contratado",
          ]}
        />
        <p className="mt-3">
          Cuando la base sea el consentimiento, podrás revocarlo sin afectar la
          licitud del tratamiento previo. Si no entregas datos necesarios para
          el contrato (por ejemplo correo de acceso), no podremos prestar el
          servicio.
        </p>
      </section>

      <section>
        <LegalH2>4. Encargados y destinatarios</LegalH2>
        <p className="mt-3">
          Podemos compartir datos con proveedores que nos ayudan a operar la
          plataforma (por ejemplo hosting, infraestructura cloud y mensajería),
          bajo instrucciones y medidas de seguridad. Hoy el aviso al cliente se
          abre en WhatsApp (wa.me); Meta/WhatsApp tiene sus propias políticas
          cuando usas su aplicación.
        </p>
        <p className="mt-3">
          No vendemos datos personales. Solo los comunicamos si es necesario
          para el servicio, por obligación legal o con tu autorización.
        </p>
      </section>

      <section>
        <LegalH2>5. Transferencias internacionales</LegalH2>
        <p className="mt-3">
          Si algún proveedor almacena o procesa datos fuera de Chile, lo haremos
          con las garantías que exige la Ley 21.719 (cláusulas contractuales u
          otros mecanismos admitidos) e informaremos cuando aplique en esta
          política o en el contrato del taller.
        </p>
      </section>

      <section>
        <LegalH2>6. Plazos de conservación</LegalH2>
        <p className="mt-3">
          Conservamos los datos mientras la cuenta del taller esté activa y el
          tiempo adicional necesario para: (i) cumplir el contrato; (ii)
          obligaciones legales o tributarias; (iii) resolver disputas; y (iv)
          seguridad. Luego se eliminan o anonimizan de forma segura, salvo
          bloqueo cuando la ley lo exija.
        </p>
      </section>

      <section>
        <LegalH2>7. Tus derechos (ARCOP y otros)</LegalH2>
        <p className="mt-3">
          Conforme a la Ley 21.719, puedes solicitar respecto de tus datos:
        </p>
        <LegalList
          items={[
            "Acceso e información sobre el tratamiento",
            "Rectificación o actualización",
            "Cancelación o eliminación",
            "Oposición a determinados tratamientos",
            "Portabilidad, cuando corresponda",
            "Bloqueo u otras medidas que la ley reconozca",
          ]}
        />
        <p className="mt-3">
          Para ejercerlos, escribe por WhatsApp al{" "}
          <strong className="text-white/90">+56 9 8187 5498</strong> indicando
          tu nombre, el derecho que quieres ejercer y un medio de contacto. Te
          responderemos dentro de los plazos legales (en general hasta 30 días
          corridos, prorrogables según la normativa). También podrás acudir a la
          Agencia de Protección de Datos Personales (APDP) cuando esté operativa
          conforme a la ley.
        </p>
      </section>

      <section>
        <LegalH2>8. Seguridad</LegalH2>
        <p className="mt-3">
          Aplicamos medidas técnicas y organizativas razonables (control de
          acceso, cifrado en tránsito cuando el proveedor lo permite, gestión de
          sesiones y minimización de datos). Ningún sistema es 100 % seguro: si
          ocurre una vulneración relevante, actuaremos según la Ley 21.719
          (contención, registro y, cuando corresponda, aviso a titulares y/o
          autoridad).
        </p>
      </section>

      <section>
        <LegalH2>9. Menores de edad</LegalH2>
        <p className="mt-3">
          El servicio está orientado a talleres y profesionales mayores de 18
          años. No está dirigido a niños.
        </p>
      </section>

      <section>
        <LegalH2>10. Cambios a esta política</LegalH2>
        <p className="mt-3">
          Podemos actualizar este texto para reflejar cambios del producto o de
          la ley. La fecha de “Última actualización” indica la versión vigente.
          Si el cambio es sustancial, avisaremos por medios razonables (por
          ejemplo aviso en el panel o correo al taller).
        </p>
      </section>
    </LegalShell>
  );
}
