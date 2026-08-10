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
