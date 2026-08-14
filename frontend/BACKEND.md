# Contrato API — Motor Ping (v2)

Documento para el backend (Claude + amigo) y alineación con el frontend.  
Frontend: Next.js. Marca: **Motor Ping**.

**Base URL sugerida:** la que usen en Railway/Render  
**Auth:** JWT Bearer  
**Teléfonos:** siempre normalizados **sin `+`**, solo dígitos (ej. `56912345678`)

---

## Principios de producto

1. **El aviso al cliente es el corazón del producto.**  
   Hoy el frontend usa `wa.me` (gratis, sin Meta).  
   La arquitectura debe permitir pasar a **envío automático por WhatsApp Business API** sin rehacer el frontend.

2. **Quién hace qué importa.** El usuario no es “el taller entero”: son personas (dueño / mecánico) dentro de un taller.

3. **El vehículo es entidad**, no un string libre. El historial por patente es lo que engancha al taller.

---

## 1. WhatsApp / avisos (arquitectura)

### Flujo correcto

Cada vez que una orden **cambia de estado** (endpoint de status), el backend:

1. Actualiza el status de la orden  
2. Crea una fila en **`notifications`** (aviso pendiente/registrado)  
3. Según config del taller:
   - `whatsappMode = "link"` → el frontend arma `wa.me` con el mensaje de esa notificación  
   - `whatsappMode = "api"` → el backend envía solo vía Meta API y marca la notificación como `sent`

Así Martín no cambia de pantallas cuando activen la API: solo cambia de dónde sale el envío.

### Tabla `notifications`

| Campo | Tipo | Notas |
|-------|------|--------|
| id | uuid | |
| workshopId | uuid | |
| orderId | uuid | |
| clientId | uuid | |
| channel | `whatsapp` | por ahora |
| toPhone | string | normalizado |
| message | string | texto final |
| status | `pending` \| `link_ready` \| `sent` \| `failed` | |
| triggeredByUserId | uuid | quién movió el estado |
| createdAt | datetime | |
| sentAt | datetime? | |

### Workshop config

| Campo | Tipo | Notas |
|-------|------|--------|
| whatsappMode | `link` \| `api` | default: `link` |

### Frontend hoy

- Botón “Avisar por WhatsApp” abre `wa.me` usando el mensaje de la notificación (o uno generado igual).  
- **No** es envío automático todavía, pero el backend **sí registra** el aviso.

---

## 2. Usuarios (no solo el taller)

### `workshops`
| Campo | Tipo |
|-------|------|
| id | uuid |
| name | string |
| phone | string |
| whatsappMode | `link` \| `api` |
| createdAt | datetime |

### `users`
| Campo | Tipo | Notas |
|-------|------|--------|
| id | uuid | |
| workshopId | uuid | |
| name | string | |
| email | string | único |
| passwordHash | string | |
| role | `owner` \| `mechanic` | |
| createdAt | datetime | |

### Auth

- `POST /auth/login` → `{ token, workshop, user }`  
  (`user` puede ignorarse al inicio en el frontend; ya viene listo)
- `GET /auth/me` → `{ workshop, user }`
- `POST /auth/register` → **NO público**. Solo alta interna/admin (ustedes dan de alta talleres).  
  No hay pantalla `/register` en el frontend a propósito.

---

## 3. Vehículo estructurado + cliente

### `clients`
| Campo | Tipo |
|-------|------|
| id | uuid |
| workshopId | uuid |
| name | string |
| phone | string (normalizado) |
| notes | string? |

### `vehicles`
| Campo | Tipo | Notas |
|-------|------|--------|
| id | uuid | |
| workshopId | uuid | |
| clientId | uuid | dueño actual |
| plate | string | patente normalizada (mayúsculas, sin espacios) |
| brand | string? | marca |
| model | string? | modelo |
| createdAt | datetime | |

### Órdenes

La orden referencia `vehicleId`.  
Para no romper el frontend, la API **siempre** incluye:

```json
"vehicleOrItem": "Toyota Corolla · Patente ABCD12"
```

armado en el backend a partir de marca/modelo/patente.

---

## 4. Estados de orden (lista completa)

```
recibido
en_diagnostico
esperando_aprobacion
en_reparacion
esperando_repuesto
listo
entregado
```

Los dos críticos que faltaban:

- `esperando_aprobacion` — el auto está quieto esperando el “sí” del cliente  
- `esperando_repuesto` — quieto esperando pieza  

Son los momentos con más llamadas desesperadas.

### `?open=true` (definición fija)

Órdenes cuyo status **no** es `entregado`.

---

## 5. Endpoints MVP

### Auth
- `POST /auth/login` — `{ email, password }` → `{ token, workshop, user }`
- `GET /auth/me`
- `POST /auth/register` — **protegido (admin)**; no expuesto al público

### Clientes
- `GET /clients`
- `POST /clients` — `{ name, phone, notes? }`
  - si el teléfono es el de una ficha **archivada**, la revive (mismo `id`, historial intacto) y responde `201`
- `GET /clients/:id`
- `PATCH /clients/:id`
- `DELETE /clients/:id` — **archiva** la ficha → `204` sin cuerpo
  - no borra: la ficha desaparece de `GET /clients` y de sus autos en `GET /vehicles`, pero sus órdenes quedan
  - `409` si el cliente tiene órdenes abiertas (hay que cerrarlas o archivarlas primero)
  - `404` si ya estaba archivada

### Vehículos
- `GET /vehicles?clientId=`
- `POST /vehicles` — `{ clientId, plate, brand?, model? }`
- `GET /vehicles/:id`
- `PATCH /vehicles/:id`
- `GET /vehicles/:id/history` — órdenes previas de esa patente (clave de retención)

### Órdenes
- `GET /orders`  
  - query: `?open=true` \| `?status=`  
  - **paginación:** `?page=1&limit=20`  
  - cada orden **incluye embebido:**
    ```json
    "client": { "id", "name", "phone" },
    "vehicle": { "id", "plate", "brand", "model" },
    "vehicleOrItem": "string armado"
    ```

- `POST /orders` — body:
  ```json
  {
    "clientId": "...",
    "vehicleId": "...",
    "title": "Revisión de frenos",
    "description": "...",
    "estimatedAt": "2026-08-10",
    "status": "recibido"
  }
  ```
  (alternativa aceptada al inicio: enviar `plate/brand/model` y el backend crea/asocia el vehículo)

- `GET /orders/:id` — mismo shape embebido + `photos[]` + últimos `notifications`

- `PATCH /orders/:id` — **solo campos** (title, description, estimatedAt, etc.)  
  **No cambia status. No dispara aviso.**

- `DELETE /orders/:id` — **archiva** la orden → `204` sin cuerpo  
  Es para la orden que se creó mal, no para la que se terminó (esa se cierra con `status: entregado`).  
  Sale del tablero y del historial del vehículo; los avisos ya enviados quedan. `404` si ya estaba archivada.

- `POST /orders/:id/status` — body: `{ "status": "listo" }`  
  - valida transición  
  - guarda historial  
  - crea `notification`  
  - si `whatsappMode=api`, intenta envío automático

### Fotos (varias)
- Storage: **Cloudflare R2** (o S3-compatible). No guardar en disco del servidor.
- `POST /orders/:id/photos` — multipart → agrega a la lista  
- `GET` ya trae:
  ```json
  "photos": [{ "id", "url", "createdAt" }]
  ```
- Dejar de usar `photoUrl` singular.

### Notificaciones (para el frontend link)
- `GET /orders/:id/notifications/latest` — último aviso `link_ready`/`pending` con `message` + `toPhone`  
  (o incluirlo en `GET /orders/:id`)

---

## 6. Historial de cambios

Tabla `order_events` (mínimo):

| Campo | Tipo |
|-------|------|
| id | uuid |
| orderId | uuid |
| userId | uuid |
| type | `status_changed` \| `field_updated` \| `photo_added` |
| fromStatus | string? |
| toStatus | string? |
| meta | json? |
| createdAt | datetime |

Responde: “¿quién movió esta orden a listo?”

---

## 7. Formato de respuestas

Éxito:
```json
{ "data": { ... } }
```

Lista paginada:
```json
{
  "data": [ ... ],
  "meta": { "page": 1, "limit": 20, "total": 53 }
}
```

Error:
```json
{ "error": { "message": "Cliente no encontrado", "code": "NOT_FOUND" } }
```

**Desde el 13-08-2026 no hay que adivinar los nombres de los campos.** Cada ruta declara
su respuesta, así que `openapi.json` —el archivo versionado en la raíz del repo— dice
exactamente qué sale de cada una, no solo qué entra. Es el contrato: en producción `/docs`
está cerrada, y ese archivo se regenera en el mismo commit que cambia la API (hay un test
que falla si quedó viejo). Si un campo no está ahí, no existe.

---

## 8. Prioridad de construcción (backend)

1. Workshops + users + login  
2. Clients + vehicles  
3. Orders + `POST /status` + `order_events` + `notifications`  
4. Photos en R2 (múltiples)  
5. Paginación + CORS al frontend  
6. (Después) WhatsApp Business API + switch `whatsappMode`

---

## 9. Frontend actual (Martín)

| Ruta | Estado |
|------|--------|
| `/` | Landing |
| `/login` | Login visual (sin `/register` público) |
| `/panel` | Órdenes abiertas (mock) |
| `/panel/clientes` | Clientes |
| `/panel/nueva-orden` | Formulario |
| `/panel/ordenes/[id]` | Detalle + botón wa.me |

Cuando la API esté up: avisar URL base + cómo va el Bearer token.

---

## 10. Qué se acepta de la crítica de Claude

| Punto | Decisión |
|-------|----------|
| wa.me no es aviso automático | Correcto. Queda como modo `link`; arquitectura lista para `api` |
| users aparte del workshop | Adoptado |
| vehículo estructurado | Adoptado; `vehicleOrItem` se sigue devolviendo armado |
| estados esperando_aprobacion / esperando_repuesto | Adoptados |
| PATCH vs POST status | Adoptado |
| client embebido en orders | Adoptado |
| register no público | Adoptado (alta interna) |
| fotos en R2 + múltiples | Adoptado |
| historial + paginación + open definido + phone normalizado | Adoptado |

---

## 11. Panel de Solve (admin de plataforma)

Agregado el 12-08-2026. Todo lo de esta sección está construido, probado y en `/docs`.

### Los tres roles

`user.role` viene en la respuesta del login y en `GET /auth/me`. **No hace falta
adivinarlo por el correo** — si el frontend todavía trata `demo@tallertrack.cl` como
admin, eso se puede borrar.

| | `owner` | `mechanic` | `platform_admin` |
|---|---|---|---|
| `/orders`, `/clients`, `/vehicles`, `/statuses` | ✅ | ✅ | lista vacía |
| `/users` (equipo del taller) | ✅ | **403** | 403 |
| `/admin/*` | 403 | 403 | ✅ |

En pantallas: el mecánico ve Hoy, Clientes, Nueva orden y el detalle de la orden con
mover estado y avisar. El dueño ve todo eso **más Equipo**. El admin no entra al panel del
taller: entra al panel de Solve.

### Administrar la cuenta de un taller

```
POST   /admin/workshops                     alta de taller + su dueño en un paso
GET    /admin/workshops                     lista (?archived=true trae los dados de baja)
PATCH  /admin/workshops/:id                 corregir nombre/teléfono, o suspender con active:false
DELETE /admin/workshops/:id                 dar de baja (no borra nada)
POST   /admin/workshops/:id/restore         devolverlo con todo adentro
POST   /admin/workshops/:id/owner-password  clave nueva para el dueño que la perdió
GET    /admin/workshops/:id/users           el equipo de ese taller
POST   /admin/workshops/:id/users           crear una cuenta de respaldo ahí adentro
GET    /admin/accounts                      las cuentas de Solve
POST   /admin/accounts                      crear otra cuenta de Solve
PATCH  /admin/accounts/:id                  renombrar o apagar una (nunca la propia)
```

`GET /admin/workshops` devuelve cada taller con `ownerEmail` y `ordersCount`.

### El plan del taller y el tope de mecánicos

Agregado el 13-08-2026. **Las dos cosas que el panel prometía y el backend no tenía ya
existen.**

`plan` es `"basico"` o `"plus"`, viaja en **todo** taller que devuelve la API (login,
`GET /auth/me`, lista y ficha del panel) y se elige en el alta (`plan` en
`POST /admin/workshops`, por defecto `basico`) o se cambia después con
`PATCH /admin/workshops/:id`. Cualquier otro valor es 422.

El tope **lo aplica el servidor**: un taller en `basico` no puede tener más de **3
mecánicos activos**. `POST /users`, `PATCH /users/:id` con `active: true` y
`POST /admin/workshops/:id/users` responden **409** cuando ya está lleno. El dueño no
ocupa cupo y los apagados tampoco. Nunca es retroactivo: un taller que se pasa a `basico`
con cinco mecánicos se queda con los cinco: lo único que no puede es sumar al sexto.

### Suspensión, con o sin fecha

Todo taller que devuelve la API trae estos cuatro campos, y significan una sola cosa cada
uno:

```jsonc
{
  "active": false,                          // ¿puede entrar HOY? (no es "qué dice la columna")
  "status": "suspended",                    // "active" | "suspended" | "deleted"
  "suspendedUntil": "2026-09-01T00:00:00Z", // null si no hay fecha de término
  "suspendIndefinite": false                // true = suspendido hasta que alguien lo reactive
}
```

Cómo se pide, con `PATCH /admin/workshops/:id`:

| Cuerpo | Qué hace |
|---|---|
| `{ "active": false }` | suspende hasta que alguien lo reactive |
| `{ "active": false, "suspendedUntil": "2026-09-01T00:00:00Z" }` | suspende y **vuelve solo** ese día |
| `{ "active": true }` | reactiva y borra la fecha |
| `suspendedUntil` sola, o con `active: true` | **422** |
| `suspendedUntil` en el pasado | **422** |

Mientras dura, la gente de ese taller recibe 401 en el login y en cada pedido. Cumplida la
fecha vuelve a entrar sin que nadie toque nada — **y con el mismo token de antes**: la
suspensión corta el paso, no cierra sesiones.

### Lo que trae el plan Plus (13-08-2026)

Tres rutas, todas con **403 si el taller no es `plus`**. Esconder el botón con
`isPlusPlan()` no basta: sin el 403, cualquiera con sesión pide la URL a mano y se lleva
gratis lo que el taller de al lado paga.

```
GET /reports/weekly     el resumen de los últimos 7 días
GET /exports/clients    la libreta de clientes, en CSV
GET /exports/history    todo lo que pasó por el taller, en CSV
```

**`/reports/weekly`** devuelve exactamente el tipo `WeeklyReport` que ya está escrito en
`src/lib/plus-reports.ts`. Cómo se cuenta cada número:

| Campo | Qué cuenta |
|---|---|
| `ordersOpen` | todo lo que no está `entregado` |
| `ordersWaiting` | `esperando_aprobacion` + `esperando_repuesto` — el taller detenido esperando a alguien |
| `ordersReady` | `listo`: terminado, esperando que el cliente lo venga a buscar |
| `ordersCreated` | órdenes abiertas en los últimos 7 días |
| `ordersDelivered` | entregadas en los últimos 7 días (se cuenta por el **evento** de entrega, no por `updated_at`: corregirle el título a una orden vieja no la vuelve a entregar) |
| `byStatus` | desglose de **las abiertas**, no de todas: responde "qué tengo hoy", no "qué hice alguna vez" |
| `openOrders` | las abiertas, **de la más vieja a la más nueva** — la que lleva más tiempo adentro es la que hay que mirar primero |

`from` y `to` son la ventana, en ISO con Z.

**Los CSV** salen con `Content-Disposition` (nombre de archivo incluido), separador **`;`** y
BOM al principio. No es capricho: con comas, Excel en configuración regional chilena mete
todo en una sola columna, y sin BOM los acentos y las eñes salen rotos. `apiDownload` ya
lee el nombre del header.

### Mirar un taller (solo lectura)

```
GET /admin/workshops/:id                    la ficha, con sus señales
GET /admin/workshops/:id/orders             sus órdenes, mismos filtros que /orders
GET /admin/workshops/:id/orders/:ordenId    la orden con bitácora y todos sus avisos
```

Por esta puerta **no se escribe**: un PATCH o un DELETE responden 405. Para arreglarle
algo a un taller están las acciones de arriba.

La ficha:

```jsonc
{ "data": {
  "id": "...", "name": "Taller San Cristóbal", "phone": "56987654321",
  "whatsappMode": "link", "plan": "basico",
  "active": true, "status": "active",
  "suspendedUntil": null, "suspendIndefinite": false,
  "createdAt": "2026-08-01T12:00:00Z", "deletedAt": null,
  "stats": {
    "ordersTotal": 57,
    "ordersOpen": 4,
    "lastActivityAt": "2026-08-12T14:03:00Z",   // null si nunca hubo una orden
    "noticesPending": 2,                         // avisos en link_ready que nunca se enviaron
    "usersActive": 3
  }
}}
```

El detalle de una orden trae los campos de siempre más:

```jsonc
{
  "events": [
    { "id": "...", "type": "cambio_de_estado", "fromStatus": "recibido",
      "toStatus": "en_reparacion", "userName": "Marcela",
      "createdAt": "2026-08-12T13:40:00Z" }
  ],
  "notifications": [
    { "id": "...", "toPhone": "56911111111", "message": "Hola Juan...",
      "status": "link_ready", "createdAt": "...", "sentAt": null }
  ]
}
```

`userName` es `null` si esa cuenta ya no existe. `notifications` viene completo y en
orden, no solo el último como en el panel del taller.

Los talleres dados de baja se siguen mirando. El interno de Solve no: da 404.

Abrir la ficha queda anotado en `admin_audit` (`workshop_viewed`) con quién entró. Es
transparente para el frontend, pero conviene saberlo: mirar un taller deja rastro.
