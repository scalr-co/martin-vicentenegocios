# Lo que el frontend todavía no conecta

12-08-2026. Escrito para Martín.

El backend está en producción y probado. Hay tres pantallas del frontend que no lo usan:
funcionan sobre datos guardados en el navegador, así que se ven bien y no muestran nada
real. Esta es la lista, con el endpoint que ya existe para cada una.

El contrato completo de cada endpoint está en `frontend/BACKEND.md`, sección 11.

---

## 1. El panel de admin muestra talleres inventados

`src/app/panel/admin/page.tsx` lee de `src/lib/admin-accounts.ts`, que es una semilla
guardada en `localStorage` bajo `motorping_admin_accounts_demo_v2`: "Taller El Pino /
Carlos Pérez", "Ana Rojas". Ninguno existe.

Los talleres de verdad están en:

| Lo que hace hoy la pantalla | Endpoint real |
|---|---|
| `listWorkshopAccounts()` | `GET /admin/workshops` — trae `ownerEmail` y `ordersCount` |
| `createWorkshopAccount()` | `POST /admin/workshops` — crea taller y dueño en un paso |
| Suspender | `PATCH /admin/workshops/:id` con `{ "active": false }` |
| Reactivar | `PATCH /admin/workshops/:id` con `{ "active": true }` |
| Eliminar | `DELETE /admin/workshops/:id` (no borra: se deshace con `POST /admin/workshops/:id/restore`) |
| Ver los dados de baja | `GET /admin/workshops?archived=true` |

Dos cosas de esa pantalla no tienen respaldo en el backend y hay que sacarlas o pedirlas:

- **El plan `basico` / `plus`** (`src/lib/plans.ts`). No existe el campo `plan` en la
  tabla `workshops`. El límite de 3 mecánicos que muestra el panel hoy no lo aplica nadie.
- **"Suspender hasta una fecha"** (`suspendedUntil`, `suspendIndefinite`). La suspensión
  es un interruptor: queda fuera hasta que alguien la reactive. No hay vencimiento.

Si los quieren de verdad, se agregan al backend — pero conviene decidirlo antes de que un
taller vea una promesa que el sistema no cumple.

## 2. La pantalla de mecánicos no da de alta a nadie

`src/app/panel/mecanicos/` lee de `src/lib/mechanics.ts` (`localStorage`,
`motorping_mechanics_demo`). Un mecánico creado ahí no puede entrar al sistema: no existe
en la base.

| Lo que hace hoy | Endpoint real |
|---|---|
| `listMechanics()` | `GET /users` — trae todo el equipo, incluidos los apagados (`active: false`) |
| `createMechanic()` | `POST /users` — nombre, correo y clave; el rol lo pone el backend |
| `updateMechanic()` | `PATCH /users/:id` — nombre, y `active` para apagar y encender |
| `deleteMechanic()` | **no existe, a propósito.** Apagar con `active: false` en vez de borrar: el nombre del mecánico cuelga del historial de cada orden que movió |
| (falta) | `POST /users/:id/password` — clave nueva, y le cierra la sesión que tuviera abierta |

Todo `/users` es **solo del dueño**. Un `mechanic` recibe 403 en cada una.

## 3. El panel no distingue al dueño del mecánico

Hoy los dos ven la misma barra, con el mismo link "Mecánicos"
(`src/components/panel-shell.tsx`). El día que esa pantalla llame a `/users` de verdad, el
mecánico va a apretar el link y recibir un 403.

`user.role` viene en el login y en `GET /auth/me`. Con eso:

- Mostrar "Mecánicos" solo si `role === "owner"`.
- Cortar el acceso directo a `/panel/mecanicos` con un guard, igual que hace `AdminGuard`
  con `/panel/admin`.

El mecánico se queda con Hoy, Clientes, Nueva orden y el detalle de la orden — mover
estado y avisar por WhatsApp, que es su pega.

## 4. El correo `demo@tallertrack.cl` abre el panel de admin

`isAdmin()` en `src/lib/auth.ts` cae a comparar el correo cuando el rol no calza, y
`resolveSessionRole()` fuerza `platform_admin` para ese correo en el login.

El daño real es cosmético: el backend le da 403 a todo lo de `/admin/*`, así que quien
entre con ese correo ve un panel vacío. Pero ya no hace falta — el login devuelve
`role: "platform_admin"` desde que existen las cuentas de verdad — y mientras esté ahí, el
panel de administración es una pantalla que se abre con un correo conocido.

---

## Lo que sí está conectado y funciona

`/panel`, `/panel/clientes`, `/panel/nueva-orden`, `/panel/ordenes/[id]` y `/login`. Esas
cuatro pantallas ya hablan con la API.

## Pantallas nuevas que el backend ya soporta

Con la vista de soporte (sección 11 de `BACKEND.md`) se puede armar, dentro del panel de
admin, la ficha de un taller: sus señales, sus órdenes y el detalle de una orden con la
bitácora de quién la movió y si el WhatsApp salió. Es lo que hoy no tenemos cuando un
taller llama con un problema.
