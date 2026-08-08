# TallerTrack — Backend

API del sistema de ordenes de trabajo para talleres mecanicos. El mecanico mueve la orden de
estado y el sistema deja redactado el mensaje para avisarle al cliente por WhatsApp.

Frontend: Next.js, a cargo de Martin. Backend: este repositorio.

## Estado

**Fase 3 — el producto funcionando.** El taller ya opera de punta a punta: se abre la orden,
se mueve de estado, queda registrado quien la movio y el aviso al cliente sale escrito. Falta
subir fotos y desplegar.

| Fase | Contenido | Estado |
|---|---|---|
| F0 | Esqueleto, `/health`, `/docs`, CORS | ✅ (falta desplegar) |
| F1 | workshops, users, login, roles | ✅ |
| F2 | clients, vehicles, historial por patente | ✅ |
| F3 | orders, `POST /orders/:id/status`, eventos y avisos | ✅ |
| F4 | Fotos en Cloudflare R2 | ⬜ |
| F5 | `GET /statuses` ✅, filtros y paginacion fina | 🟡 |
| F6 | Envio automatico por WhatsApp API (modo `api`) | ⬜ |

Los estados de una orden, en orden: `recibido`, `en_diagnostico`, `esperando_aprobacion`,
`en_reparacion`, `esperando_repuesto`, `listo`, `entregado`. `GET /orders?open=true` trae
todo lo que no este `entregado`.

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

La lista de endpoints **siempre esta al dia en `/docs`**. Se genera sola desde el codigo, asi que
no puede quedar desactualizada. Ahi puedes ver cada campo y probar las llamadas sin escribir nada.

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
- Fechas: ISO 8601 en UTC. `estimatedAt` es fecha sin hora.
- Paginacion: `?page=&limit=`, con tope de 100 por pagina.
- Los cambios que rompan compatibilidad se avisan aca antes de subirlos.

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

## Migraciones

Crear o actualizar las tablas:

```bash
.venv/Scripts/python.exe -m alembic upgrade head
```

Despues de cambiar un modelo, generar la migracion correspondiente:

```bash
.venv/Scripts/python.exe -m alembic revision --autogenerate -m "que cambio"
```
