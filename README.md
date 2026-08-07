# TallerTrack — Backend

API del sistema de ordenes de trabajo para talleres mecanicos. El mecanico mueve la orden de
estado y el sistema deja redactado el mensaje para avisarle al cliente por WhatsApp.

Frontend: Next.js, a cargo de Martin. Backend: este repositorio.

## Estado

**Fase 1 — identidad.** Ya se puede entrar: `POST /auth/login` y `GET /auth/me` funcionan,
con talleres, usuarios y roles. Clientes, vehiculos y ordenes vienen en las fases siguientes.

| Fase | Contenido | Estado |
|---|---|---|
| F0 | Esqueleto, `/health`, `/docs`, CORS | ✅ (falta desplegar) |
| F1 | workshops, users, login, roles | 🟡 en curso |
| F2 | clients, vehicles, historial por patente | ⬜ |
| F3 | orders, `POST /orders/:id/status`, eventos y avisos | ⬜ |
| F4 | Fotos en Cloudflare R2 | ⬜ |
| F5 | Paginacion fina, filtros, `GET /statuses` | ⬜ |

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
