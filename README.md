# TallerTrack — Backend

API del sistema de ordenes de trabajo para talleres mecanicos. El mecanico mueve la orden de
estado y el sistema deja redactado el mensaje para avisarle al cliente por WhatsApp.

Frontend: Next.js, a cargo de Martin. Backend: este repositorio.

## Estado

**Fase 0 — esqueleto.** Funciona `/health`, la documentacion en `/docs` y el CORS.
Las entidades (talleres, usuarios, clientes, vehiculos, ordenes) vienen en las fases siguientes.

| Fase | Contenido | Estado |
|---|---|---|
| F0 | Esqueleto, `/health`, `/docs`, CORS, despliegue | 🟡 en curso |
| F1 | workshops, users, login, roles | ⬜ |
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
| `FRONTEND_ORIGINS` | Dominios autorizados a llamar la API, separados por coma |
