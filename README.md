# Motor Ping — Backend

API del sistema de ordenes de trabajo para talleres mecanicos. El mecanico mueve la orden de
estado y el sistema deja redactado el mensaje para avisarle al cliente por WhatsApp.

Frontend: Next.js, a cargo de Martin. Backend: este repositorio.

## Estado

**Fase 3 — el producto funcionando.** El taller ya opera de punta a punta: se abre la orden,
se mueve de estado, queda registrado quien la movio y el aviso al cliente sale escrito. Falta
subir fotos y desplegar.

| Fase | Contenido | Estado |
|---|---|---|
| F0 | Esqueleto, `/health`, `/docs`, CORS | ✅ |
| F1 | workshops, users, login, roles | ✅ |
| F2 | clients, vehicles, historial por patente | ✅ |
| F3 | orders, `POST /orders/:id/status`, eventos y avisos | ✅ |
| F4 | Fotos en Cloudflare R2 | ⬜ |
| F5 | `GET /statuses`, filtros y paginacion | ✅ |
| F6 | Envio automatico por WhatsApp API (modo `api`) | ⬜ |
| F7 | Equipo del taller, suspension y baja de talleres | ✅ |
| F8 | Planes con tope de mecanicos, suspension con fecha, contrato de salida | ✅ |
| F9 | Ventajas del plan Plus: resumen semanal y exportar a CSV | ✅ |

Los estados de una orden, en orden: `recibido`, `en_diagnostico`, `esperando_aprobacion`,
`en_reparacion`, `esperando_repuesto`, `listo`, `entregado`. `GET /orders?open=true` trae
todo lo que no este `entregado`.

El panel busca con `GET /orders?search=`, por **patente o por nombre del cliente**, con un
pedazo basta y da igual como se escriba: `?search=abcd12` y `?search=perez` sirven. Se
combina con `?status=` y con `?open=true`. El `total` del `meta` cuenta lo filtrado.

Dos cosas que **todavia no** estan y conviene no esperar: el campo `photos` de las ordenes
(llega en F4, con las fotos de verdad) y el envio automatico de WhatsApp (F6: hoy todos los
talleres funcionan en modo `link`).

### Como se avisa al cliente

Cada estado trae un mensaje escrito por defecto. Al mover la orden, el backend deja ese texto
listo en `notifications` y el frontend abre `wa.me` con el.

El mecanico puede **editarlo antes de enviarlo**. Casi siempre sirve el de siempre, pero
cuando aparece un imprevisto —"le encontramos una fuga en el radiador"— tiene que poder
contarlo. Por eso `POST /orders/:id/status` acepta un `message` opcional que reemplaza la
plantilla, y en `notifications` se guarda siempre el texto que de verdad salio, no el
predeterminado.

`POST /orders/:id/status` responde con las dos cosas juntas, para no tener que pedir nada mas
antes de abrir WhatsApp:

```jsonc
{
  "data": {
    "order": { "id": "...", "status": "listo", "vehicleOrItem": "Toyota Corolla · Patente ABCD12" },
    "notification": {
      "id": "...",
      "toPhone": "56911111111",
      "message": "Hola Juan, tu Toyota Corolla (ABCD12) ya está listo para retirar en Taller Los Alerces.",
      "status": "link_ready"
    }
  }
}
```

Con eso el frontend arma `https://wa.me/{toPhone}?text={message}`. Si la orden ya estaba en
ese estado, `notification` viene en `null` y no se crea nada: repetirlo seria mandarle al
cliente el mismo mensaje dos veces.

Despues de abrir WhatsApp, el frontend cierra el ciclo con `POST /notifications/:id/sent`.
El aviso pasa de `link_ready` a `sent` y queda la hora. Sin ese paso ningun aviso llega
nunca a `sent`, y el registro no puede responder "esto se le dijo, y cuando". Llamarlo dos
veces no cambia la hora original, asi que el frontend puede reintentar sin miedo.

Los estados no se escriben a mano en el frontend: `GET /statuses` devuelve la lista con su
etiqueta y si cierra la orden.

```jsonc
{ "data": [ { "key": "en_diagnostico", "label": "En diagnóstico", "isOpen": true } ] }
```

## Para Martin

La lista de endpoints **siempre esta al dia en `/docs`**, corriendo el backend en tu maquina. Se
genera sola desde el codigo, asi que no puede quedar desactualizada: ahi ves cada campo y pruebas
las llamadas sin escribir nada.

**En produccion `/docs` esta cerrada** (y `/openapi.json` tambien). Con ella abierta cualquiera
lista las rutas del panel de administracion desde internet. Si no quieres levantar el backend,
el archivo `openapi.json` del repo tiene el mismo contenido y se regenera con
`python scripts/exportar_openapi.py`.

Convenciones del contrato:

```jsonc
// Un recurso
{ "data": { } }

// Una lista
{ "data": [ ], "meta": { "page": 1, "limit": 20, "total": 57 } }

// Un error
{ "error": { "message": "Orden no encontrada", "code": "NOT_FOUND" } }
```

- Telefonos: solo digitos, sin `+`. Ejemplo `56912345678`.
- Patentes: mayusculas y sin espacios. Ejemplo `ABCD12`.
- Rut del cliente: **opcional**, sin puntos y con guion. Ejemplo `12345678-5`. Se puede mandar como
  lo escriba el mecanico (`12.345.678-5`) y la API lo deja en ese formato; si el digito verificador
  no calza responde **422**, que es justo para lo que sirve. `GET /clients?search=` tambien busca
  por rut, con puntos o sin ellos.
- Fechas: ISO 8601 en UTC. `estimatedAt` es fecha sin hora.
- Paginacion: `?page=&limit=`, con tope de 100 por pagina.
- Los cambios que rompan compatibilidad se avisan aca antes de subirlos.

### Cuentas

El dueno del taller administra a su equipo en `/users`: da de alta mecanicos, los apaga y
los enciende, y les resetea la clave. Un `mechanic` recibe 403 en todo `/users`, y un
dueno que pida por alguien de otro taller recibe 404.

Apagar a alguien **no lo borra**: sigue saliendo en `GET /users` con `active: false`,
porque su nombre cuelga del historial de las ordenes que movio. Cambiarle la clave le
cierra la sesion que tuviera abierta.

El panel de Solve suspende talleres con `PATCH /admin/workshops/:id` y `active: false`, y
los da de baja con `DELETE /admin/workshops/:id`. Ninguna de las dos borra datos: la
primera se deshace con `active: true` y la segunda con `POST /admin/workshops/:id/restore`.
`GET /admin/workshops` muestra los suspendidos y esconde los dados de baja; con
`?archived=true` trae solo estos ultimos.

Un taller suspendido deja fuera a su gente **en el siguiente request**, no cuando venza el
token.

### Quien ve que

Tres roles, una sola aplicacion. El backend ya los separa; el frontend solo tiene que
mostrar lo que corresponde.

| | `owner` | `mechanic` | `platform_admin` |
|---|---|---|---|
| `/orders`, `/clients`, `/vehicles`, `/statuses` | si | si | vacio (su taller es el interno) |
| `/users` (el equipo del taller) | si | **403** | 403 |
| `/admin/*` (talleres y cuentas de Solve) | 403 | 403 | si |

El rol viene en el login y en `GET /auth/me`, dentro de `user.role`. No hace falta
adivinarlo por el correo.

### Mirar un taller

Cuando el taller llama con un problema, Solve puede mirar lo que tiene entre manos. Es
**solo lectura**: por esta puerta no se mueve una orden ni se corrige una ficha. Para eso
estan las acciones del panel, que dejan su rastro.

```
GET /admin/workshops/:id                    la ficha, con sus senales
GET /admin/workshops/:id/orders             sus ordenes, con los mismos filtros del panel
GET /admin/workshops/:id/orders/:ordenId    la orden con su bitacora y todos sus avisos
```

La ficha contesta "esta funcionando o esta atascado" sin entrar orden por orden:

```jsonc
{ "data": {
  "id": "...", "name": "Taller San Cristobal", "phone": "56987654321",
  "whatsappMode": "link", "active": true,
  "createdAt": "2026-08-01T12:00:00Z", "deletedAt": null,
  "stats": {
    "ordersTotal": 57,        // todas, igual que el ordersCount de la lista
    "ordersOpen": 4,          // lo que no esta entregado ni archivado
    "lastActivityAt": "2026-08-12T14:03:00Z",
    "noticesPending": 2,      // avisos que quedaron en link_ready y nunca se enviaron
    "usersActive": 3
  }
}}
```

`noticesPending` es la senal mas util: un taller que mueve ordenes y deja los avisos sin
enviar no esta usando el producto, esta peleando con el.

El listado de ordenes acepta los mismos `?open=`, `?status=`, `?search=`, `?page=` y
`?limit=` que `GET /orders`, y devuelve las ordenes con la misma forma. El detalle agrega
dos listas que el panel del taller no muestra completas:

```jsonc
{ "data": {
  "id": "...", "title": "Frenos", "status": "listo", "client": { }, "vehicle": { },
  "events": [
    { "id": "...", "type": "cambio_de_estado", "fromStatus": "recibido",
      "toStatus": "en_reparacion", "userName": "Marcela",
      "createdAt": "2026-08-12T13:40:00Z" }
  ],
  "notifications": [
    { "id": "...", "toPhone": "56911111111", "message": "Hola Juan...",
      "status": "link_ready", "createdAt": "...", "sentAt": null }
  ]
}}
```

`userName` queda en `null` si esa cuenta ya no existe: el evento sobrevive a la persona.

Los talleres **dados de baja tambien se miran**: cuando uno se va, lo que interesa es
entender por que. El taller interno de Solve no, igual que no sale en la lista.

Abrir la ficha de un taller **queda anotado** en `admin_audit` con la accion
`workshop_viewed` y el nombre de quien entro. Se anota una vez cada media hora por
persona y taller: recargar la pagina no llena el registro de ruido. Los listados y el
detalle no anotan nada, porque para llegar a ellos hay que pasar por la ficha.

## Correr en tu maquina

Con Docker, que levanta la API y la base de datos juntas:

```bash
docker compose up
```

Sin Docker:

```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev]"    # Windows
uvicorn app.main:app --reload
```

En ambos casos la API queda en <http://localhost:8000> y la documentacion en
<http://localhost:8000/docs>.

## Tests

```bash
.venv/Scripts/python.exe -m pytest
```

## Configuracion

Copia `.env.example` como `.env` y completa los valores. El `.env` real nunca se sube:
este repositorio es publico.

| Variable | Para que sirve |
|---|---|
| `ENTORNO` | `desarrollo` o `produccion` |
| `DATABASE_URL` | Conexion a la base de datos |
| `FRONTEND_ORIGINS` | Dominios autorizados a llamar la API, separados por coma |
| `JWT_SECRET` | Clave con que se firman los tokens de sesion |
| `ADMIN_API_KEY` | Clave para dar de alta talleres. Vacia deja el alta cerrada |

En produccion la aplicacion **no arranca** si `JWT_SECRET` sigue siendo el valor de ejemplo:
esta escrito en este repositorio publico, asi que cualquiera podria fabricarse un token.

## Desplegar

Paso a paso en [docs/desplegar-en-railway.md](docs/desplegar-en-railway.md): crear el
proyecto, enchufar Postgres, las variables que hay que poner y como dar de alta el primer
taller.

Lo que conviene saber de antemano:

- La imagen corre `alembic upgrade head` antes de levantar la API. Si las migraciones
  fallan, el contenedor no arranca: mejor eso que una API respondiendo 500 contra una base
  que no calza con el codigo.
- El puerto lo decide el hosting por la variable `PORT`; en local sigue siendo 8000.
- La URL de Postgres que entregan los proveedores (`postgresql://...`) se traduce sola al
  driver instalado. No hay que editarla a mano.

## Migraciones

Crear o actualizar las tablas:

```bash
.venv/Scripts/python.exe -m alembic upgrade head
```

Despues de cambiar un modelo, generar la migracion correspondiente:

```bash
.venv/Scripts/python.exe -m alembic revision --autogenerate -m "que cambio"
```
