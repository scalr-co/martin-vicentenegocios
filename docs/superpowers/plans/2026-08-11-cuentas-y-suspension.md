# Cuentas y suspension — Plan de implementacion

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Que el dueno de un taller administre su propio equipo y que Solve pueda suspender, dar de baja y restaurar talleres completos, mas crear la segunda cuenta de administracion desde el panel.

**Architecture:** Dos niveles separados. Un router nuevo `/users` detras de `solo_dueno` para el equipo del taller, y ampliaciones a `/admin` detras de `solo_admin_plataforma` para lo de Solve. El corte de acceso no necesita codigo nuevo: `usuario_actual` ya consulta la base en cada request y rechaza a quien tenga `active=False` o cuyo taller lo tenga. Suspender es `Workshop.active=False`; dar de baja agrega `Workshop.deleted_at`, igual que se archivan clientes y ordenes.

**Tech Stack:** Python 3.14, FastAPI, SQLAlchemy 2.0 (`Mapped`/`mapped_column`), Pydantic v2, Alembic, pytest. Base de datos: SQLite en tests y desarrollo, Postgres en produccion.

**Spec:** `docs/superpowers/specs/2026-08-11-cuentas-y-suspension-design.md`

## Global Constraints

- **Idioma del codigo:** todo en espanol y **sin tildes** — nombres, docstrings y comentarios. Es la convencion de todo el repositorio (`crear_taller_con_dueno`, `_taller_o_404`, "dueno", "mecanico").
- **Contrato de respuestas:** un recurso es `{"data": {...}}`, una lista es `{"data": [...]}`, y con paginacion agrega `"meta"`. Los errores los traduce `app/errores.py` a `{"error": {"message", "code"}}` — nunca se arma ese formato a mano en una ruta.
- **Esquemas:** todos heredan de `app.schemas.base.Esquema`, que convierte `snake_case` a `camelCase` hacia afuera. Se serializa siempre con `.model_dump(by_alias=True)`.
- **Texto escrito por personas:** usar los tipos `Texto` / `TextoOpcional` de `app/schemas/base.py`, que recortan espacios antes de medir el largo.
- **Migraciones a mano, nunca `--autogenerate`.** Las columnas se agregan dentro de `with op.batch_alter_table('tabla') as lote:` porque desarrollo es SQLite. Modelo de referencia: `alembic/versions/f2a9c4d8e1b3_version_de_sesion.py`.
- **Cabeza de Alembic al empezar:** `f2a9c4d8e1b3`. La migracion de este plan va encima.
- **Nunca se borran filas.** Archivar es escribir `deleted_at`.
- **Nada de fabricar tokens a mano en los tests:** se entra con `entrar(cliente, email, clave)`, que hace login de verdad.
- **Correr los tests:** `.venv/Scripts/python.exe -m pytest`
- **Largo minimo de clave:** 8 caracteres para usuarios de taller, **12 para cuentas de administracion de plataforma** (`crear_admin` ya lo exige: "es la cuenta con mas poder del sistema").

## Estructura de archivos

| Archivo | Responsabilidad | Tarea |
|---|---|---|
| `app/models/workshop.py` | agregar `deleted_at` | 1 |
| `alembic/versions/<rev>_baja_de_talleres.py` | la columna en la base | 1 |
| `app/models/admin_audit.py` | constantes de las acciones nuevas | 3 |
| `app/models/__init__.py` | exportarlas | 3 |
| `app/services/altas.py` | `correo_libre()` y `crear_admin()` compartidos | 2 |
| `scripts/crear_admin.py` | pasa a importar de `services/altas.py` | 2 |
| `app/schemas/admin.py` | `active` en `TallerEdicion`, esquemas de cuentas | 3, 9 |
| `app/schemas/user.py` **(nuevo)** | esquemas del equipo del taller | 5 |
| `app/routes/users.py` **(nuevo)** | el equipo del taller, detras de `solo_dueno` | 5, 6, 7 |
| `app/routes/admin.py` | suspension, baja, restore, equipo, cuentas | 3, 4, 8, 9 |
| `app/main.py` | registrar el router nuevo | 5 |
| `tests/test_users.py` **(nuevo)** | el equipo del taller y su aislamiento | 5, 6, 7 |
| `tests/test_admin.py` | lo de Solve | 3, 4, 8, 9, 10 |

---

### Task 1: La columna `deleted_at` en los talleres

**Files:**
- Modify: `app/models/workshop.py`
- Create: `alembic/versions/a7c3e9f1d4b2_baja_de_talleres.py`
- Test: `tests/test_migraciones.py` (ya existe y corre todas las migraciones)

**Interfaces:**
- Consumes: nada.
- Produces: `Workshop.deleted_at: Mapped[datetime | None]`. Las tareas 4 y 8 lo usan.

- [ ] **Step 1: Escribir el test que falla**

Agregar al final de `tests/test_migraciones.py`:

```python
def test_los_talleres_tienen_fecha_de_baja(sesion):
    """Dar de baja un taller no borra nada: escribe la fecha, como en clientes."""
    from app.models.base import ahora
    from tests.conftest import crear_taller

    taller = crear_taller(sesion)
    assert taller.deleted_at is None

    taller.deleted_at = ahora()
    sesion.commit()

    assert taller.deleted_at is not None
```

- [ ] **Step 2: Correr el test y verificar que falla**

Run: `.venv/Scripts/python.exe -m pytest tests/test_migraciones.py::test_los_talleres_tienen_fecha_de_baja -v`
Expected: FAIL con `AttributeError: 'Workshop' object has no attribute 'deleted_at'`

- [ ] **Step 3: Agregar la columna al modelo**

En `app/models/workshop.py`, despues del campo `internal` y antes de `created_by_user_id`:

```python
    # La baja definitiva: el taller se fue. Sale de la lista del panel pero sus ordenes,
    # sus clientes y su historial por patente quedan enteros, por si vuelve. Se guarda la
    # fecha y no un booleano por lo mismo que en clientes: cuando se pregunta por un
    # taller que falta, lo que se quiere saber es cuando dejo de estar.
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
```

- [ ] **Step 4: Correr el test y verificar que pasa**

Run: `.venv/Scripts/python.exe -m pytest tests/test_migraciones.py -v`
Expected: PASS

- [ ] **Step 5: Escribir la migracion a mano**

Crear `alembic/versions/a7c3e9f1d4b2_baja_de_talleres.py`:

```python
"""fecha de baja en workshops, para dar de baja un taller sin borrarlo

Revision ID: a7c3e9f1d4b2
Revises: f2a9c4d8e1b3
Create Date: 2026-08-11

Nulo -el valor de todos los talleres que ya existen- significa vigente, que es lo
correcto: ninguno de los que estan hoy se ha dado de baja.

No se borra de verdad a proposito: del taller cuelgan sus usuarios, sus clientes, sus
vehiculos, sus ordenes y los avisos que ya salieron por WhatsApp. Un taller que deja de
pagar tiene que poder volver y encontrar su historial donde lo dejo.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a7c3e9f1d4b2'
down_revision: Union[str, Sequence[str], None] = 'f2a9c4d8e1b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('workshops') as lote:
        lote.add_column(sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('workshops') as lote:
        lote.drop_column('deleted_at')
```

- [ ] **Step 6: Correr las migraciones y la suite entera**

Run: `.venv/Scripts/python.exe -m alembic upgrade head`
Expected: termina sin error.

Run: `.venv/Scripts/python.exe -m pytest`
Expected: todo verde.

- [ ] **Step 7: Commit**

```bash
git add app/models/workshop.py alembic/versions/a7c3e9f1d4b2_baja_de_talleres.py tests/test_migraciones.py
git commit -m "Fecha de baja en los talleres, para darlos de baja sin borrarlos"
```

---

### Task 2: Un solo chequeo de correo repetido

Hoy el mismo `select` esta escrito dos veces: dentro de `crear_taller_con_dueno` y dentro de `crear_admin`. Este plan agrega dos puertas de alta mas; sin unificarlo ahora, quedan cuatro copias que se van a separar.

**Files:**
- Modify: `app/services/altas.py`
- Modify: `scripts/crear_admin.py`
- Test: `tests/test_admin.py`

**Interfaces:**
- Consumes: nada.
- Produces:
  - `correo_libre(sesion: Session, email: str) -> str` — devuelve el correo normalizado (recortado y en minusculas) o levanta `HTTPException` 409.
  - `crear_admin(sesion, nombre: str, email: str, clave: str) -> User` — se muda desde `scripts/crear_admin.py` sin cambiar su firma.
  - `NoSePudoCrear` — la excepcion, tambien mudada.
  - `LARGO_MINIMO_DE_CLAVE_ADMIN = 12`

Las tareas 5, 8 y 9 usan `correo_libre`. La tarea 9 usa `crear_admin`.

- [ ] **Step 1: Escribir el test que falla**

Agregar a `tests/test_admin.py`:

```python
def test_el_correo_se_guarda_en_minusculas_y_sin_espacios(cliente, token_admin, sesion):
    """El dueno escribe su correo como le sale. Si una puerta normaliza y otra no,
    el mismo correo entra dos veces y despues nadie puede entrar."""
    respuesta = alta_de_taller(cliente, token_admin, email="  Marcela@SanCristobal.CL ")
    assert respuesta.status_code == 201, respuesta.text

    guardado = sesion.scalar(select(User).where(User.role == "owner"))
    assert guardado.email == "marcela@sancristobal.cl"


def test_no_se_puede_repetir_el_correo_aunque_cambie_la_capitalizacion(cliente, token_admin):
    alta_de_taller(cliente, token_admin, email="marcela@sancristobal.cl")
    repetido = alta_de_taller(
        cliente, token_admin, email="MARCELA@sancristobal.cl", workshopName="Otro Taller"
    )

    assert repetido.status_code == 409
    assert repetido.json()["error"]["code"] == "CONFLICT"
```

- [ ] **Step 2: Correr los tests y verificar que fallan**

Run: `.venv/Scripts/python.exe -m pytest tests/test_admin.py -k "correo" -v`
Expected: FAIL — `crear_taller_con_dueno` no normaliza, guarda `"  Marcela@SanCristobal.CL "` tal cual.

- [ ] **Step 3: Escribir `correo_libre` y mudar `crear_admin`**

En `app/services/altas.py`, agregar arriba (despues de los imports):

```python
LARGO_MINIMO_DE_CLAVE_ADMIN = 12


class NoSePudoCrear(Exception):
    """El correo ya esta tomado o la clave no sirve. La levanta el script de consola."""


def correo_libre(sesion: Session, email: str) -> str:
    """Deja el correo listo para guardar, o levanta 409 si ya esta tomado.

    Normaliza antes de comparar: el correo es unico en todo el sistema y es con lo que se
    entra. Si una puerta guarda "Ana@taller.cl" y otra busca "ana@taller.cl", el mismo
    correo entra dos veces y el login deja de saber a quien se refiere.
    """
    email = email.strip().lower()
    if sesion.scalar(select(User).where(User.email == email)) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un usuario con ese correo",
        )
    return email
```

Reemplazar el chequeo que hoy vive dentro de `crear_taller_con_dueno` por una llamada:

```python
    email = correo_libre(sesion, datos.email)
```

y usar esa variable `email` al construir el `User` del dueno, en vez de `datos.email`.

Agregar `crear_admin` al mismo archivo:

```python
def crear_admin(sesion: Session, nombre: str, email: str, clave: str) -> User:
    """Una cuenta de administracion de la plataforma. No hace commit.

    Vive aca y no en el script porque se entra por dos puertas: la consola del servidor
    para la primera cuenta, y `POST /admin/accounts` -con sesion de admin- para las
    siguientes.
    """
    if len(clave) < LARGO_MINIMO_DE_CLAVE_ADMIN:
        raise NoSePudoCrear(
            f"La clave necesita al menos {LARGO_MINIMO_DE_CLAVE_ADMIN} caracteres: es la "
            "cuenta con mas poder del sistema."
        )

    admin = User(
        workshop_id=taller_interno(sesion).id,
        name=nombre.strip(),
        email=correo_libre(sesion, email),
        password_hash=hashear(clave),
        role=ROL_ADMIN_PLATAFORMA,
    )
    sesion.add(admin)
    return admin
```

Ajustar los imports de `app/services/altas.py` para incluir `ROL_ADMIN_PLATAFORMA`.

**Cuidado con un cambio de comportamiento:** `crear_admin` levantaba `NoSePudoCrear` cuando el correo estaba repetido, y ahora `correo_libre` levanta `HTTPException`. El script tiene que seguir imprimiendo un mensaje legible en vez de reventar. Se resuelve en el paso siguiente.

- [ ] **Step 4: Dejar el script como una cascara**

Reemplazar el cuerpo de `scripts/crear_admin.py` conservando su docstring, e importando de services:

```python
from fastapi import HTTPException  # noqa: E402

from app.db import FabricaDeSesiones  # noqa: E402
from app.services.altas import (  # noqa: E402
    LARGO_MINIMO_DE_CLAVE_ADMIN as LARGO_MINIMO_DE_CLAVE,
)
from app.services.altas import NoSePudoCrear, crear_admin  # noqa: E402
```

El alias mantiene el nombre `LARGO_MINIMO_DE_CLAVE` que el script ya exportaba, por si algo lo importa de ahi.

En `main()`, envolver la llamada para traducir el 409 a un mensaje de consola:

```python
    with FabricaDeSesiones() as sesion:
        try:
            admin = crear_admin(sesion, opciones.nombre, opciones.email, opciones.password)
        except NoSePudoCrear as error:
            print(f"No se creo la cuenta: {error}")
            return 1
        except HTTPException as error:
            print(f"No se creo la cuenta: {error.detail}")
            return 1
        sesion.commit()
        print(f"Cuenta de administracion creada: {admin.email}")
```

con `from fastapi import HTTPException` arriba.

Borrar del script la definicion de `crear_admin`, la de `NoSePudoCrear` y sus imports que ya no se usan (`select`, `hashear`, `User`, `ROL_ADMIN_PLATAFORMA`, `taller_interno`). `tests/test_admin.py` hace `from scripts.crear_admin import NoSePudoCrear, crear_admin` y sigue funcionando, porque los nombres quedan ligados al modulo del script.

- [ ] **Step 5: Correr la suite entera**

Run: `.venv/Scripts/python.exe -m pytest`
Expected: todo verde, incluidos los dos tests nuevos y los que ya existian de `crear_admin`.

- [ ] **Step 6: Commit**

```bash
git add app/services/altas.py scripts/crear_admin.py tests/test_admin.py
git commit -m "Un solo chequeo de correo repetido para todas las puertas de alta"
```

---

### Task 3: Suspender y reactivar un taller

**Files:**
- Modify: `app/models/admin_audit.py`
- Modify: `app/models/__init__.py`
- Modify: `app/schemas/admin.py`
- Modify: `app/routes/admin.py`
- Test: `tests/test_admin.py`

**Interfaces:**
- Consumes: `_anotar`, `_taller_o_404` (ya existen en `app/routes/admin.py`).
- Produces: constantes `ACCION_TALLER_SUSPENDIDO`, `ACCION_TALLER_REACTIVADO`, `ACCION_TALLER_DADO_DE_BAJA`, `ACCION_TALLER_RESTAURADO`, `ACCION_USUARIO_CREADO`, `ACCION_CUENTA_ADMIN_CREADA`, `ACCION_CUENTA_ADMIN_EDITADA`. Las tareas 4, 8 y 9 las usan.

- [ ] **Step 1: Escribir los tests que fallan**

Agregar a `tests/test_admin.py`:

```python
def test_suspender_un_taller_deja_a_su_gente_fuera(cliente, token_admin, sesion):
    """El taller que deja de pagar no puede entrar. Sus datos no se tocan."""
    creado = alta_de_taller(cliente, token_admin).json()["data"]
    taller_id = creado["workshop"]["id"]
    token_dueno = entrar(cliente, "marcela@sancristobal.cl", clave="una-clave-larga-de-verdad")

    assert cliente.get("/clients", headers=con_token(token_dueno)).status_code == 200

    suspension = cliente.patch(
        f"/admin/workshops/{taller_id}",
        json={"active": False},
        headers=con_token(token_admin),
    )
    assert suspension.status_code == 200
    assert suspension.json()["data"]["active"] is False

    # El token que ya tenia en la mano deja de servir en el siguiente request.
    assert cliente.get("/clients", headers=con_token(token_dueno)).status_code == 401
    # Y tampoco puede volver a entrar.
    assert cliente.post(
        "/auth/login",
        json={"email": "marcela@sancristobal.cl", "password": "una-clave-larga-de-verdad"},
    ).status_code == 401


def test_reactivar_devuelve_el_acceso_con_todo_adentro(cliente, token_admin):
    creado = alta_de_taller(cliente, token_admin).json()["data"]
    taller_id = creado["workshop"]["id"]

    cliente.patch(
        f"/admin/workshops/{taller_id}",
        json={"active": False},
        headers=con_token(token_admin),
    )
    reactivado = cliente.patch(
        f"/admin/workshops/{taller_id}",
        json={"active": True},
        headers=con_token(token_admin),
    )

    assert reactivado.status_code == 200
    assert reactivado.json()["data"]["active"] is True
    assert entrar(cliente, "marcela@sancristobal.cl", clave="una-clave-larga-de-verdad")


def test_la_suspension_queda_anotada_con_su_autor(cliente, token_admin, sesion):
    from app.models import AdminAudit

    taller_id = alta_de_taller(cliente, token_admin).json()["data"]["workshop"]["id"]
    cliente.patch(
        f"/admin/workshops/{taller_id}",
        json={"active": False},
        headers=con_token(token_admin),
    )

    anotado = sesion.scalar(
        select(AdminAudit).where(AdminAudit.action == "workshop_suspended")
    )
    assert anotado is not None
    assert anotado.workshop_id == taller_id
    assert anotado.actor_user_id is not None
```

- [ ] **Step 2: Correr los tests y verificar que fallan**

Run: `.venv/Scripts/python.exe -m pytest tests/test_admin.py -k "suspender or reactivar or anotada" -v`
Expected: FAIL — `TallerEdicion` no acepta `active`, asi que el 422 o el taller sigue activo.

- [ ] **Step 3: Agregar las constantes de auditoria**

En `app/models/admin_audit.py`, junto a las tres que ya estan:

```python
ACCION_TALLER_SUSPENDIDO = "workshop_suspended"
ACCION_TALLER_REACTIVADO = "workshop_reactivated"
ACCION_TALLER_DADO_DE_BAJA = "workshop_archived"
ACCION_TALLER_RESTAURADO = "workshop_restored"
ACCION_USUARIO_CREADO = "user_created"
ACCION_CUENTA_ADMIN_CREADA = "admin_created"
ACCION_CUENTA_ADMIN_EDITADA = "admin_updated"
```

En `app/models/__init__.py`, agregarlas al `import` desde `app.models.admin_audit` y a `__all__`.

- [ ] **Step 4: Aceptar `active` en `TallerEdicion`**

En `app/schemas/admin.py`:

```python
class TallerEdicion(Esquema):
    """Solo lo que se corrige a mano. El nombre sale en el WhatsApp que lee el cliente.

    `active` en falso suspende el taller: nadie de ahi entra, y sus datos quedan enteros.
    """

    name: Texto | None = Field(default=None, min_length=2, max_length=120)
    phone: str | None = Field(default=None, min_length=8, max_length=20)
    active: bool | None = None
```

con `from app.schemas.base import Esquema, Texto`.

- [ ] **Step 5: Anotar la suspension en `editar_taller`**

En `app/routes/admin.py`, dentro de `editar_taller`, reemplazar la llamada unica a `_anotar` por esto, **despues** del bucle que aplica los cambios:

```python
    # La suspension no es "una edicion mas": deja a un taller entero sin poder entrar.
    # Merece su propia linea en el registro, que es lo que se lee cuando alguien
    # pregunta por que no puede trabajar.
    if "active" in cambios:
        _anotar(
            sesion,
            admin,
            ACCION_TALLER_SUSPENDIDO if not cambios["active"] else ACCION_TALLER_REACTIVADO,
            taller_id=taller.id,
        )

    otros = sorted(campo for campo in cambios if campo != "active")
    if otros:
        _anotar(
            sesion,
            admin,
            ACCION_TALLER_EDITADO,
            taller_id=taller.id,
            detalle=", ".join(otros),
        )
```

**Cuidado:** el diccionario `cambios` que hay hoy filtra con `if valor is not None`, y `False` **no** es `None`, asi que `active: false` entra bien. No cambiar ese filtro.

Agregar `ACCION_TALLER_REACTIVADO` y `ACCION_TALLER_SUSPENDIDO` al import de `app.models` en `admin.py`.

- [ ] **Step 6: Correr los tests y verificar que pasan**

Run: `.venv/Scripts/python.exe -m pytest tests/test_admin.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add app/models/admin_audit.py app/models/__init__.py app/schemas/admin.py app/routes/admin.py tests/test_admin.py
git commit -m "Suspender y reactivar un taller desde el panel, con su rastro"
```

---

### Task 4: Dar de baja, restaurar y ocultar de la lista

**Files:**
- Modify: `app/routes/admin.py`
- Test: `tests/test_admin.py`

**Interfaces:**
- Consumes: `Workshop.deleted_at` (tarea 1), constantes de auditoria (tarea 3).
- Produces: `_taller_o_404(sesion, taller_id, incluir_dados_de_baja: bool = False)` — la firma cambia; la tarea 8 la usa.

- [ ] **Step 1: Escribir los tests que fallan**

```python
def test_dar_de_baja_saca_el_taller_de_la_lista_sin_borrar_nada(cliente, token_admin, sesion):
    taller_id = alta_de_taller(cliente, token_admin).json()["data"]["workshop"]["id"]

    baja = cliente.delete(f"/admin/workshops/{taller_id}", headers=con_token(token_admin))
    assert baja.status_code == 204

    lista = cliente.get("/admin/workshops", headers=con_token(token_admin)).json()["data"]
    assert [t for t in lista if t["id"] == taller_id] == []

    # No se borro: sigue en la base, con su fecha de baja.
    guardado = sesion.get(Workshop, taller_id)
    assert guardado is not None
    assert guardado.deleted_at is not None
    assert guardado.active is False


def test_los_dados_de_baja_se_ven_pidiendolos(cliente, token_admin):
    taller_id = alta_de_taller(cliente, token_admin).json()["data"]["workshop"]["id"]
    cliente.delete(f"/admin/workshops/{taller_id}", headers=con_token(token_admin))

    lista = cliente.get(
        "/admin/workshops?archived=true", headers=con_token(token_admin)
    ).json()["data"]

    assert [t["id"] for t in lista] == [taller_id]


def test_el_suspendido_si_sale_en_la_lista(cliente, token_admin):
    """Es el que se va a reactivar: esconderlo lo volveria irrecuperable desde el panel."""
    taller_id = alta_de_taller(cliente, token_admin).json()["data"]["workshop"]["id"]
    cliente.patch(
        f"/admin/workshops/{taller_id}",
        json={"active": False},
        headers=con_token(token_admin),
    )

    lista = cliente.get("/admin/workshops", headers=con_token(token_admin)).json()["data"]

    assert [t["active"] for t in lista if t["id"] == taller_id] == [False]


def test_restaurar_devuelve_el_taller_entero(cliente, token_admin):
    taller_id = alta_de_taller(cliente, token_admin).json()["data"]["workshop"]["id"]
    cliente.delete(f"/admin/workshops/{taller_id}", headers=con_token(token_admin))

    vuelto = cliente.post(
        f"/admin/workshops/{taller_id}/restore", headers=con_token(token_admin)
    )

    assert vuelto.status_code == 200
    assert vuelto.json()["data"]["active"] is True
    assert entrar(cliente, "marcela@sancristobal.cl", clave="una-clave-larga-de-verdad")


def test_repetir_la_baja_no_mueve_la_fecha(cliente, token_admin, sesion):
    """El frontend puede reintentar sin miedo, igual que con los avisos enviados.

    La fecha es la respuesta a "cuando se fue": pisarla con la de hoy la vuelve mentira.
    """
    taller_id = alta_de_taller(cliente, token_admin).json()["data"]["workshop"]["id"]

    cliente.delete(f"/admin/workshops/{taller_id}", headers=con_token(token_admin))
    primera = sesion.get(Workshop, taller_id).deleted_at

    segunda = cliente.delete(f"/admin/workshops/{taller_id}", headers=con_token(token_admin))

    assert segunda.status_code == 204
    assert sesion.get(Workshop, taller_id).deleted_at == primera


def test_el_taller_interno_de_solve_no_se_toca(cliente, token_admin, sesion):
    """Suspenderlo dejaria a la propia administracion fuera del sistema: las cuentas de
    Solve viven en ese taller, y `usuario_actual` exige que el taller este activo."""
    interno = sesion.scalar(select(Workshop).where(Workshop.internal.is_(True)))
    assert interno is not None

    suspension = cliente.patch(
        f"/admin/workshops/{interno.id}",
        json={"active": False},
        headers=con_token(token_admin),
    )
    baja = cliente.delete(
        f"/admin/workshops/{interno.id}", headers=con_token(token_admin)
    )

    assert suspension.status_code == 404
    assert baja.status_code == 404
    assert sesion.get(Workshop, interno.id).active is True
    # Y quien administra sigue entrando.
    assert entrar(cliente, "vicente@solve.cl", clave=CLAVE_DEL_ADMIN)


def test_el_taller_interno_no_sale_en_la_lista(cliente, token_admin):
    """No es un taller mecanico: no tiene ordenes ni clientes que mirar."""
    lista = cliente.get("/admin/workshops", headers=con_token(token_admin)).json()["data"]

    assert "Solve" not in [t["name"] for t in lista]


def test_restaurar_uno_que_no_estaba_de_baja_no_falla(cliente, token_admin):
    taller_id = alta_de_taller(cliente, token_admin).json()["data"]["workshop"]["id"]

    respuesta = cliente.post(
        f"/admin/workshops/{taller_id}/restore", headers=con_token(token_admin)
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["data"]["active"] is True
```

- [ ] **Step 2: Correr y verificar que fallan**

Run: `.venv/Scripts/python.exe -m pytest tests/test_admin.py -k "baja or restaurar or suspendido_si_sale" -v`
Expected: FAIL con 405 — no existen `DELETE /admin/workshops/{id}` ni `/restore`.

- [ ] **Step 3: Que `_taller_o_404` sepa de los dados de baja**

En `app/routes/admin.py`, reemplazar la funcion:

```python
def _taller_o_404(
    sesion: Session, taller_id: str, incluir_dados_de_baja: bool = False
) -> Workshop:
    """El taller del panel. Nunca el interno de Solve: ese no se administra desde aca.

    Por defecto ignora los dados de baja, para que una peticion vieja no reviva sin
    querer un taller que ya se fue. Solo `restore` pide verlos.
    """
    condiciones = [Workshop.id == taller_id, Workshop.internal.is_(False)]
    if not incluir_dados_de_baja:
        condiciones.append(Workshop.deleted_at.is_(None))

    taller = sesion.scalar(select(Workshop).where(*condiciones))
    if taller is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Taller no encontrado")
    return taller
```

- [ ] **Step 4: Escribir la baja y la restauracion**

Al final de `app/routes/admin.py`:

```python
@router.delete("/workshops/{taller_id}", status_code=status.HTTP_204_NO_CONTENT)
def dar_de_baja(
    taller_id: str,
    admin: User = Depends(solo_admin_plataforma),
    sesion: Session = Depends(obtener_sesion),
):
    """El taller se fue. Sale de la lista y nadie de ahi entra, pero no se borra nada.

    Sus ordenes, sus clientes y su historial por patente quedan enteros: si vuelve en dos
    meses, `restore` le devuelve todo donde lo dejo. Es la misma decision que con los
    clientes y las ordenes, y por la misma razon.
    """
    taller = _taller_o_404(sesion, taller_id, incluir_dados_de_baja=True)

    # Repetirlo no mueve la fecha original: es la respuesta a "cuando se fue".
    if taller.deleted_at is None:
        taller.deleted_at = ahora()
        taller.active = False
        _anotar(sesion, admin, ACCION_TALLER_DADO_DE_BAJA, taller_id=taller.id)
        sesion.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/workshops/{taller_id}/restore")
def restaurar(
    taller_id: str,
    admin: User = Depends(solo_admin_plataforma),
    sesion: Session = Depends(obtener_sesion),
):
    """Devuelve a la vida un taller dado de baja, con todo lo suyo adentro.

    Pedir lo que ya se cumple no es un error: sobre un taller vigente lo deja activo y
    responde igual, para que el panel pueda reintentar sin miedo.
    """
    taller = _taller_o_404(sesion, taller_id, incluir_dados_de_baja=True)

    if taller.deleted_at is not None or not taller.active:
        taller.deleted_at = None
        taller.active = True
        _anotar(sesion, admin, ACCION_TALLER_RESTAURADO, taller_id=taller.id)
        sesion.commit()

    return {"data": WorkshopSalida.model_validate(taller).model_dump(by_alias=True)}
```

Agregar arriba: `from fastapi import Response`, `from app.models.base import ahora`, y las constantes `ACCION_TALLER_DADO_DE_BAJA` y `ACCION_TALLER_RESTAURADO` al import de `app.models`.

- [ ] **Step 5: Filtrar la lista**

En `listar_talleres`, cambiar la firma y la condicion:

```python
@router.get("/workshops", dependencies=[Depends(solo_admin_plataforma)])
def listar_talleres(
    archived: bool = Query(default=False),
    sesion: Session = Depends(obtener_sesion),
):
```

y reemplazar el `.where(Workshop.internal.is_(False))` de la consulta final por:

```python
    condiciones = [Workshop.internal.is_(False)]
    # Los suspendidos si salen: son los que se van a reactivar. Los dados de baja no,
    # salvo que se pidan, para que la lista responda "quien esta usando esto" y no
    # "quien lo uso alguna vez".
    condiciones.append(
        Workshop.deleted_at.is_not(None) if archived else Workshop.deleted_at.is_(None)
    )

    filas = sesion.execute(
        select(Workshop, correo_del_dueno, ordenes)
        .where(*condiciones)
        .order_by(Workshop.created_at.desc())
    ).all()
```

Agregar `Query` al import de fastapi.

- [ ] **Step 6: Correr los tests**

Run: `.venv/Scripts/python.exe -m pytest tests/test_admin.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add app/routes/admin.py tests/test_admin.py
git commit -m "Dar de baja y restaurar talleres, sin borrar una sola fila"
```

---

### Task 5: El dueno crea y lista a su equipo

**Files:**
- Create: `app/schemas/user.py`
- Create: `app/routes/users.py`
- Modify: `app/main.py`
- Test: `tests/test_users.py` (nuevo)

**Interfaces:**
- Consumes: `solo_dueno` (`app/security/dependencias.py`), `correo_libre` (tarea 2).
- Produces: `UsuarioEntrada`, `UsuarioEdicion`, `UsuarioSalida`, `_del_taller(sesion, usuario, usuario_id) -> User`. Las tareas 6, 7 y 8 los usan.

- [ ] **Step 1: Escribir los tests que fallan**

Crear `tests/test_users.py`:

```python
"""El equipo del taller: quien trabaja aca y quien ya no.

Lo administra el dueno, no Solve. El taller no puede quedar esperando a que le contesten
para dar de alta al mecanico que empieza el lunes.

La regla que sostiene todo lo de aca: un dueno solo alcanza a la gente de SU taller. Al
tocar a alguien de otro recibe 404 y no 403, porque un 403 confirmaria que ese id existe.
"""

from tests.conftest import CLAVE_DE_PRUEBA, con_token, entrar

CLAVE_NUEVA = "clave-nueva-del-mecanico"


def nuevo_mecanico(cliente, token, **cambios):
    cuerpo = {
        "name": "Pedro Soto",
        "email": "pedro@taller.cl",
        "password": "una-clave-de-verdad",
    }
    cuerpo.update(cambios)
    return cliente.post("/users", json=cuerpo, headers=con_token(token))


def test_el_dueno_crea_un_mecanico_y_el_mecanico_entra(cliente, sesion, dueno):
    token = entrar(cliente, dueno.email)

    creado = nuevo_mecanico(cliente, token)

    assert creado.status_code == 201, creado.text
    datos = creado.json()["data"]
    assert datos["role"] == "mechanic"
    assert datos["active"] is True
    assert "passwordHash" not in datos
    assert entrar(cliente, "pedro@taller.cl", clave="una-clave-de-verdad")


def test_el_dueno_no_puede_fabricarse_otro_dueno(cliente, sesion, dueno):
    """El rol lo pone el sistema. Si el cuerpo pudiera elegirlo, cualquier dueno se
    clonaria a si mismo y la guarda del ultimo dueno activo dejaria de servir."""
    token = entrar(cliente, dueno.email)

    creado = nuevo_mecanico(cliente, token, role="owner")

    assert creado.status_code == 201
    assert creado.json()["data"]["role"] == "mechanic"


def test_no_se_repite_un_correo_de_otro_taller(cliente, sesion, dueno, dueno_vecino):
    """El correo es unico en todo el sistema: es con lo que se entra, sin elegir taller."""
    token = entrar(cliente, dueno.email)

    creado = nuevo_mecanico(cliente, token, email=dueno_vecino.email)

    assert creado.status_code == 409
    assert creado.json()["error"]["code"] == "CONFLICT"


def test_el_dueno_ve_a_su_equipo_entero(cliente, sesion, dueno, mecanico):
    token = entrar(cliente, dueno.email)

    lista = cliente.get("/users", headers=con_token(token))

    assert lista.status_code == 200
    correos = {u["email"] for u in lista.json()["data"]}
    assert correos == {dueno.email, mecanico.email}


def test_el_dueno_no_ve_a_la_gente_del_taller_vecino(cliente, sesion, dueno, dueno_vecino):
    token = entrar(cliente, dueno.email)

    lista = cliente.get("/users", headers=con_token(token)).json()["data"]

    assert dueno_vecino.email not in {u["email"] for u in lista}


def test_el_mecanico_no_administra_el_equipo(cliente, sesion, dueno, mecanico):
    """Administrar el taller es del dueno. El mecanico opera las ordenes."""
    token = entrar(cliente, mecanico.email)

    assert cliente.get("/users", headers=con_token(token)).status_code == 403
    assert nuevo_mecanico(cliente, token, email="otro@taller.cl").status_code == 403


def test_sin_sesion_no_se_entra(cliente, sesion, dueno):
    assert cliente.get("/users").status_code == 401
```

- [ ] **Step 2: Correr y verificar que fallan**

Run: `.venv/Scripts/python.exe -m pytest tests/test_users.py -v`
Expected: FAIL con 404 — la ruta `/users` no existe.

- [ ] **Step 3: Escribir los esquemas**

Crear `app/schemas/user.py`:

```python
from datetime import datetime

from pydantic import EmailStr, Field

from app.schemas.base import Esquema, Texto

LARGO_MINIMO_DE_CLAVE = 8


class UsuarioEntrada(Esquema):
    """Alta de una persona del taller. El rol no viaja en el cuerpo: lo pone la ruta."""

    name: Texto = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=LARGO_MINIMO_DE_CLAVE, max_length=200)


class UsuarioEdicion(Esquema):
    """`active` en falso apaga a la persona sin borrarla: su nombre sigue colgando del
    historial de cada orden que movio."""

    name: Texto | None = Field(default=None, min_length=2, max_length=120)
    active: bool | None = None


class UsuarioSalida(Esquema):
    """Sin `password_hash`, por lo mismo de siempre: lo que no se expone no se filtra."""

    id: str
    name: str
    email: EmailStr
    role: str
    active: bool
    created_at: datetime
```

- [ ] **Step 4: Escribir el router**

Crear `app/routes/users.py`:

```python
"""El equipo del taller, administrado por su dueno.

Solve no participa: un taller que contrata a alguien el lunes no puede depender de que le
contesten. Para cuando el dueno se pierde existe la puerta de respaldo en
/admin/workshops/{id}/users, que si es de Solve y queda anotada.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import obtener_sesion
from app.models import ROL_MECANICO, User
from app.schemas.user import UsuarioEntrada, UsuarioSalida
from app.security.dependencias import solo_dueno
from app.security.passwords import hashear
from app.services.altas import correo_libre

router = APIRouter(prefix="/users", tags=["users"])


def _salida(usuario: User) -> dict:
    return UsuarioSalida.model_validate(usuario).model_dump(by_alias=True)


def _del_taller(sesion: Session, dueno: User, usuario_id: str) -> User:
    """La persona buscada, solo si es del mismo taller que quien pregunta.

    404 y no 403 a proposito: un 403 sobre alguien de otro taller confirmaria que ese id
    existe. Es el mismo criterio de clientes, vehiculos y ordenes.
    """
    usuario = sesion.scalar(
        select(User).where(User.id == usuario_id, User.workshop_id == dueno.workshop_id)
    )
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado"
        )
    return usuario


@router.post("", status_code=status.HTTP_201_CREATED)
def crear(
    datos: UsuarioEntrada,
    dueno: User = Depends(solo_dueno),
    sesion: Session = Depends(obtener_sesion),
):
    """Da de alta a un mecanico del taller.

    El rol lo pone esta linea y no el cuerpo del pedido: si se pudiera elegir, cualquier
    dueno se clonaria y la guarda del ultimo dueno activo no protegeria nada.
    """
    usuario = User(
        workshop_id=dueno.workshop_id,
        name=datos.name,
        email=correo_libre(sesion, datos.email),
        password_hash=hashear(datos.password),
        role=ROL_MECANICO,
    )
    sesion.add(usuario)
    sesion.commit()

    return {"data": _salida(usuario)}


@router.get("")
def listar(
    dueno: User = Depends(solo_dueno),
    sesion: Session = Depends(obtener_sesion),
):
    """Todo el equipo, incluidos los desactivados.

    Los apagados se muestran apagados en vez de esconderse: son justo los que se van a
    reactivar, y su nombre sigue apareciendo en el historial de las ordenes que movieron.
    """
    equipo = sesion.scalars(
        select(User)
        .where(User.workshop_id == dueno.workshop_id)
        .order_by(User.created_at)
    ).all()

    return {"data": [_salida(usuario) for usuario in equipo]}
```

- [ ] **Step 5: Registrar el router**

En `app/main.py`, agregar `users` al import de `app.routes` y, junto a los demas:

```python
app.include_router(users.router)
```

- [ ] **Step 6: Correr los tests**

Run: `.venv/Scripts/python.exe -m pytest tests/test_users.py -v`
Expected: PASS

Run: `.venv/Scripts/python.exe -m pytest`
Expected: todo verde.

- [ ] **Step 7: Commit**

```bash
git add app/schemas/user.py app/routes/users.py app/main.py tests/test_users.py
git commit -m "El dueno da de alta y lista a su propio equipo"
```

---

### Task 6: Desactivar y reactivar a una persona, con sus guardas

**Files:**
- Modify: `app/routes/users.py`
- Test: `tests/test_users.py`

**Interfaces:**
- Consumes: `_del_taller`, `_duenos_activos`, `UsuarioEdicion` (tarea 5).
- Produces: `PATCH /users/{id}`.

- [ ] **Step 1: Escribir los tests que fallan**

Agregar a `tests/test_users.py`:

```python
def test_desactivar_a_un_mecanico_lo_deja_fuera_al_instante(cliente, sesion, dueno, mecanico):
    token_dueno = entrar(cliente, dueno.email)
    token_mecanico = entrar(cliente, mecanico.email)
    assert cliente.get("/clients", headers=con_token(token_mecanico)).status_code == 200

    apagado = cliente.patch(
        f"/users/{mecanico.id}", json={"active": False}, headers=con_token(token_dueno)
    )

    assert apagado.status_code == 200
    assert apagado.json()["data"]["active"] is False
    # No hay que esperar a que venza su token: se cae en el siguiente request.
    assert cliente.get("/clients", headers=con_token(token_mecanico)).status_code == 401


def test_reactivar_a_un_mecanico_le_devuelve_el_acceso(cliente, sesion, dueno, mecanico):
    token = entrar(cliente, dueno.email)
    cliente.patch(f"/users/{mecanico.id}", json={"active": False}, headers=con_token(token))

    encendido = cliente.patch(
        f"/users/{mecanico.id}", json={"active": True}, headers=con_token(token)
    )

    assert encendido.status_code == 200
    assert entrar(cliente, mecanico.email)


def test_el_desactivado_sigue_saliendo_en_la_lista(cliente, sesion, dueno, mecanico):
    token = entrar(cliente, dueno.email)
    cliente.patch(f"/users/{mecanico.id}", json={"active": False}, headers=con_token(token))

    lista = cliente.get("/users", headers=con_token(token)).json()["data"]

    apagados = [u for u in lista if u["email"] == mecanico.email]
    assert apagados and apagados[0]["active"] is False


def test_nadie_se_desactiva_a_si_mismo(cliente, sesion, dueno):
    """Es el candado que deja a la persona fuera de su propia casa."""
    token = entrar(cliente, dueno.email)

    respuesta = cliente.patch(
        f"/users/{dueno.id}", json={"active": False}, headers=con_token(token)
    )

    assert respuesta.status_code == 409
    assert cliente.get("/users", headers=con_token(token)).status_code == 200


def test_el_taller_nunca_se_queda_sin_dueno_activo(cliente, sesion, dueno):
    """La invariante que sostiene todo: siempre queda un dueno que pueda administrar.

    No hace falta una guarda aparte que cuente los duenos. Quien hace la peticion ES un
    dueno activo -`solo_dueno` lo exige y `usuario_actual` verifica que este activo-, asi
    que apagando a OTRO nunca puede llegar a cero, y apagarse a si mismo esta prohibido.
    Entre esas dos cosas el conjunto no se puede vaciar.
    """
    from tests.conftest import crear_usuario

    socio = crear_usuario(sesion, dueno.workshop, email="socio@taller.cl", role="owner")
    token = entrar(cliente, dueno.email)

    apagado = cliente.patch(
        f"/users/{socio.id}", json={"active": False}, headers=con_token(token)
    )
    assert apagado.status_code == 200

    # Queda uno: el que lo apago. Y ese no se puede apagar a si mismo.
    assert cliente.patch(
        f"/users/{dueno.id}", json={"active": False}, headers=con_token(token)
    ).status_code == 409

    equipo = cliente.get("/users", headers=con_token(token)).json()["data"]
    duenos_activos = [u for u in equipo if u["role"] == "owner" and u["active"]]
    assert len(duenos_activos) == 1


def test_el_dueno_no_toca_a_nadie_del_taller_vecino(cliente, sesion, dueno, dueno_vecino):
    token = entrar(cliente, dueno.email)

    respuesta = cliente.patch(
        f"/users/{dueno_vecino.id}", json={"active": False}, headers=con_token(token)
    )

    assert respuesta.status_code == 404
    assert respuesta.json()["error"]["code"] == "NOT_FOUND"
```

- [ ] **Step 2: Correr y verificar que fallan**

Run: `.venv/Scripts/python.exe -m pytest tests/test_users.py -k "desactivar or reactivar or si_mismo or sin_dueno or vecino" -v`
Expected: FAIL con 405 — no existe `PATCH /users/{id}`.

- [ ] **Step 3: Escribir el endpoint**

En `app/routes/users.py`, agregar `UsuarioEdicion` al import de esquemas y al final del archivo:

```python
@router.patch("/{usuario_id}")
def editar(
    usuario_id: str,
    datos: UsuarioEdicion,
    dueno: User = Depends(solo_dueno),
    sesion: Session = Depends(obtener_sesion),
):
    """Cambia el nombre o enciende y apaga a una persona del taller.

    Apagar no borra: la cuenta deja de entrar y el nombre sigue colgando de cada orden
    que esa persona movio. Por eso es un interruptor y no un DELETE.
    """
    objetivo = _del_taller(sesion, dueno, usuario_id)
    cambios = datos.model_dump(exclude_unset=True)

    # El unico candado que hace falta. Quien pide esto es un dueno activo, asi que
    # apagando a otro el taller nunca se queda sin ninguno; lo unico que si lo dejaria
    # sin administracion es que se apagara a si mismo.
    if cambios.get("active") is False and objetivo.id == dueno.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No puedes desactivar tu propia cuenta",
        )

    for campo, valor in cambios.items():
        if valor is not None:
            setattr(objetivo, campo, valor)
    sesion.commit()

    return {"data": _salida(objetivo)}
```

- [ ] **Step 4: Correr los tests**

Run: `.venv/Scripts/python.exe -m pytest tests/test_users.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/routes/users.py tests/test_users.py
git commit -m "Apagar y encender a una persona del taller, sin dejar el taller sin dueno"
```

---

### Task 7: Resetear la clave de un mecanico

**Files:**
- Modify: `app/routes/users.py`
- Test: `tests/test_users.py`

**Interfaces:**
- Consumes: `_del_taller` (tarea 5), `ClaveNueva` de `app/schemas/admin.py`.
- Produces: `POST /users/{id}/password`.

- [ ] **Step 1: Escribir los tests que fallan**

```python
def test_resetear_la_clave_de_un_mecanico(cliente, sesion, dueno, mecanico):
    token = entrar(cliente, dueno.email)

    cambio = cliente.post(
        f"/users/{mecanico.id}/password",
        json={"password": CLAVE_NUEVA},
        headers=con_token(token),
    )

    assert cambio.status_code == 200
    assert entrar(cliente, mecanico.email, clave=CLAVE_NUEVA)
    vieja = cliente.post(
        "/auth/login", json={"email": mecanico.email, "password": CLAVE_DE_PRUEBA}
    )
    assert vieja.status_code == 401


def test_cambiar_la_clave_corta_la_sesion_que_estaba_abierta(cliente, sesion, dueno, mecanico):
    """Si no, quien tuviera el token de antes sigue adentro hasta 12 horas mas, con una
    clave que ya no sirve. Es lo mismo que hace el panel con la clave del dueno."""
    token_dueno = entrar(cliente, dueno.email)
    token_viejo = entrar(cliente, mecanico.email)
    assert cliente.get("/clients", headers=con_token(token_viejo)).status_code == 200

    cliente.post(
        f"/users/{mecanico.id}/password",
        json={"password": CLAVE_NUEVA},
        headers=con_token(token_dueno),
    )

    assert cliente.get("/clients", headers=con_token(token_viejo)).status_code == 401


def test_no_se_resetea_la_clave_de_otro_taller(cliente, sesion, dueno, dueno_vecino):
    token = entrar(cliente, dueno.email)

    respuesta = cliente.post(
        f"/users/{dueno_vecino.id}/password",
        json={"password": CLAVE_NUEVA},
        headers=con_token(token),
    )

    assert respuesta.status_code == 404
    # Y su clave de siempre le sigue sirviendo.
    assert entrar(cliente, dueno_vecino.email)


def test_la_clave_corta_no_se_acepta(cliente, sesion, dueno, mecanico):
    token = entrar(cliente, dueno.email)

    respuesta = cliente.post(
        f"/users/{mecanico.id}/password",
        json={"password": "corta"},
        headers=con_token(token),
    )

    assert respuesta.status_code == 422
```

- [ ] **Step 2: Correr y verificar que fallan**

Run: `.venv/Scripts/python.exe -m pytest tests/test_users.py -k "clave or password" -v`
Expected: FAIL con 405.

- [ ] **Step 3: Escribir el endpoint**

En `app/routes/users.py`, agregar `from app.schemas.admin import ClaveNueva` y:

```python
@router.post("/{usuario_id}/password")
def cambiar_clave(
    usuario_id: str,
    datos: ClaveNueva,
    dueno: User = Depends(solo_dueno),
    sesion: Session = Depends(obtener_sesion),
):
    """Para el mecanico que perdio su clave. La escribe el dueno y se la pasa.

    Sube la version de sesion: cambiar la clave tiene que cortar lo que ya estaba
    abierto, o quien tuviera el token de antes seguiria adentro con una clave muerta.
    """
    objetivo = _del_taller(sesion, dueno, usuario_id)

    objetivo.password_hash = hashear(datos.password)
    objetivo.token_version += 1
    sesion.commit()

    return {"data": _salida(objetivo)}
```

- [ ] **Step 4: Correr los tests**

Run: `.venv/Scripts/python.exe -m pytest tests/test_users.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/routes/users.py tests/test_users.py
git commit -m "El dueno resetea la clave de su mecanico y le cierra la sesion vieja"
```

---

### Task 8: La puerta de respaldo de Solve

**Files:**
- Modify: `app/routes/admin.py`
- Test: `tests/test_admin.py`

**Interfaces:**
- Consumes: `_taller_o_404` (tarea 4), `correo_libre` (tarea 2), `UsuarioSalida` (tarea 5), `ACCION_USUARIO_CREADO` (tarea 3).
- Produces: `GET` y `POST /admin/workshops/{id}/users`.

- [ ] **Step 1: Escribir los tests que fallan**

```python
def test_solve_ve_el_equipo_de_un_taller(cliente, token_admin):
    taller_id = alta_de_taller(cliente, token_admin).json()["data"]["workshop"]["id"]

    equipo = cliente.get(
        f"/admin/workshops/{taller_id}/users", headers=con_token(token_admin)
    )

    assert equipo.status_code == 200
    assert [u["email"] for u in equipo.json()["data"]] == ["marcela@sancristobal.cl"]


def test_solve_crea_un_mecanico_de_respaldo(cliente, token_admin):
    """Para cuando el dueno se pierde y hay que sacarlo del apuro."""
    taller_id = alta_de_taller(cliente, token_admin).json()["data"]["workshop"]["id"]

    creado = cliente.post(
        f"/admin/workshops/{taller_id}/users",
        json={"name": "Pedro", "email": "pedro@sancristobal.cl", "password": "clave-larga-1"},
        headers=con_token(token_admin),
    )

    assert creado.status_code == 201
    assert creado.json()["data"]["role"] == "mechanic"
    assert entrar(cliente, "pedro@sancristobal.cl", clave="clave-larga-1")


def test_solve_puede_crear_otro_dueno(cliente, token_admin):
    """El taller que perdio al suyo. Es la unica puerta que puede hacerlo."""
    taller_id = alta_de_taller(cliente, token_admin).json()["data"]["workshop"]["id"]

    creado = cliente.post(
        f"/admin/workshops/{taller_id}/users",
        json={
            "name": "Ana",
            "email": "ana@sancristobal.cl",
            "password": "clave-larga-1",
            "role": "owner",
        },
        headers=con_token(token_admin),
    )

    assert creado.status_code == 201
    assert creado.json()["data"]["role"] == "owner"


def test_el_alta_de_respaldo_queda_anotada(cliente, token_admin, sesion):
    from app.models import AdminAudit

    taller_id = alta_de_taller(cliente, token_admin).json()["data"]["workshop"]["id"]
    cliente.post(
        f"/admin/workshops/{taller_id}/users",
        json={"name": "Pedro", "email": "pedro@sancristobal.cl", "password": "clave-larga-1"},
        headers=con_token(token_admin),
    )

    anotado = sesion.scalar(select(AdminAudit).where(AdminAudit.action == "user_created"))
    assert anotado is not None and anotado.workshop_id == taller_id


def test_ni_el_dueno_ni_el_mecanico_entran_al_panel_de_solve(cliente, token_admin, sesion):
    """Administrar el propio taller no es administrar la plataforma.

    Se prueban las rutas nuevas una por una: si alguna se agrega manana sin la
    dependencia, este test es el que lo cuenta.
    """
    from tests.conftest import crear_usuario

    taller_id = alta_de_taller(cliente, token_admin).json()["data"]["workshop"]["id"]
    token_dueno = entrar(cliente, "marcela@sancristobal.cl", clave="una-clave-larga-de-verdad")

    taller_propio = sesion.scalar(select(Workshop).where(Workshop.id == taller_id))
    crear_usuario(sesion, taller_propio, email="pedro@sancristobal.cl", role="mechanic")
    token_mecanico = entrar(cliente, "pedro@sancristobal.cl")

    for token in (token_dueno, token_mecanico):
        cabeceras = con_token(token)
        assert cliente.get("/admin/workshops", headers=cabeceras).status_code == 403
        assert cliente.get(
            f"/admin/workshops/{taller_id}/users", headers=cabeceras
        ).status_code == 403
        assert cliente.post(
            f"/admin/workshops/{taller_id}/users",
            json={"name": "Colado", "email": "colado@x.cl", "password": "clave-larga-1"},
            headers=cabeceras,
        ).status_code == 403
        assert cliente.delete(
            f"/admin/workshops/{taller_id}", headers=cabeceras
        ).status_code == 403
        assert cliente.post(
            f"/admin/workshops/{taller_id}/restore", headers=cabeceras
        ).status_code == 403
        assert cliente.get("/admin/accounts", headers=cabeceras).status_code == 403
```

- [ ] **Step 2: Correr y verificar que fallan**

Run: `.venv/Scripts/python.exe -m pytest tests/test_admin.py -k "equipo or respaldo or otro_dueno" -v`
Expected: FAIL con 404.

- [ ] **Step 3: Escribir el esquema de entrada**

En `app/schemas/user.py`:

```python
class UsuarioDeRespaldoEntrada(UsuarioEntrada):
    """El alta que hace Solve. Aca si viaja el rol: es la unica puerta que puede
    devolverle un dueno al taller que perdio al suyo."""

    role: str = Field(default=ROL_MECANICO)

    @field_validator("role")
    @classmethod
    def _rol_conocido(cls, valor: str) -> str:
        if valor not in (ROL_DUENO, ROL_MECANICO):
            raise ValueError("El rol tiene que ser owner o mechanic")
        return valor
```

con `from pydantic import EmailStr, Field, field_validator` y `from app.models import ROL_DUENO, ROL_MECANICO`.

- [ ] **Step 4: Escribir los endpoints**

Al final de `app/routes/admin.py`:

```python
@router.get("/workshops/{taller_id}/users", dependencies=[Depends(solo_admin_plataforma)])
def equipo_del_taller(taller_id: str, sesion: Session = Depends(obtener_sesion)):
    """Ver quien trabaja en un taller. Es lo que se mira antes de ayudar por telefono."""
    taller = _taller_o_404(sesion, taller_id, incluir_dados_de_baja=True)

    equipo = sesion.scalars(
        select(User).where(User.workshop_id == taller.id).order_by(User.created_at)
    ).all()

    return {
        "data": [
            UsuarioSalida.model_validate(usuario).model_dump(by_alias=True)
            for usuario in equipo
        ]
    }


@router.post("/workshops/{taller_id}/users", status_code=status.HTTP_201_CREATED)
def crear_usuario_de_respaldo(
    taller_id: str,
    datos: UsuarioDeRespaldoEntrada,
    admin: User = Depends(solo_admin_plataforma),
    sesion: Session = Depends(obtener_sesion),
):
    """La puerta de respaldo: crear una cuenta dentro de un taller que no es de Solve.

    Existe para el dueno que se perdio o que perdio a su unico dueno activo. Como es
    entrar en la casa de otro, queda anotada en `admin_audit` con nombre y apellido.
    """
    taller = _taller_o_404(sesion, taller_id)

    usuario = User(
        workshop_id=taller.id,
        name=datos.name,
        email=correo_libre(sesion, datos.email),
        password_hash=hashear(datos.password),
        role=datos.role,
    )
    sesion.add(usuario)
    sesion.flush()
    _anotar(
        sesion,
        admin,
        ACCION_USUARIO_CREADO,
        taller_id=taller.id,
        usuario_id=usuario.id,
        detalle=datos.role,
    )
    sesion.commit()

    return {"data": UsuarioSalida.model_validate(usuario).model_dump(by_alias=True)}
```

Agregar los imports: `ACCION_USUARIO_CREADO` desde `app.models`, `UsuarioDeRespaldoEntrada` y `UsuarioSalida` desde `app.schemas.user`, y `correo_libre` desde `app.services.altas`.

- [ ] **Step 5: Correr los tests**

Run: `.venv/Scripts/python.exe -m pytest tests/test_admin.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add app/routes/admin.py app/schemas/user.py tests/test_admin.py
git commit -m "Puerta de respaldo: Solve crea y mira usuarios de cualquier taller"
```

---

### Task 9: Las cuentas de Solve desde el panel

**Files:**
- Modify: `app/schemas/admin.py`
- Modify: `app/routes/admin.py`
- Test: `tests/test_admin.py`

**Interfaces:**
- Consumes: `crear_admin`, `NoSePudoCrear` (tarea 2), constantes de auditoria (tarea 3).
- Produces: `POST`, `GET /admin/accounts` y `PATCH /admin/accounts/{id}`.

- [ ] **Step 1: Escribir los tests que fallan**

```python
def test_un_admin_crea_la_segunda_cuenta_desde_el_panel(cliente, token_admin):
    """Es lo que promete scripts/crear_admin.py: la primera por consola, las siguientes
    con la sesion de quien ya entro."""
    creada = cliente.post(
        "/admin/accounts",
        json={"name": "Martin", "email": "martin@solve.cl", "password": "clave-larga-de-martin"},
        headers=con_token(token_admin),
    )

    assert creada.status_code == 201
    assert creada.json()["data"]["role"] == "platform_admin"
    assert entrar(cliente, "martin@solve.cl", clave="clave-larga-de-martin")


def test_la_clave_de_un_admin_necesita_doce_caracteres(cliente, token_admin):
    """Es la cuenta con mas poder del sistema."""
    corta = cliente.post(
        "/admin/accounts",
        json={"name": "Martin", "email": "martin@solve.cl", "password": "corta-1"},
        headers=con_token(token_admin),
    )

    assert corta.status_code == 422


def test_sin_sesion_de_admin_no_se_crean_cuentas(cliente, taller, dueno):
    """Ya no hay llave que valga: la ruta con X-Admin-Key se borro por algo."""
    token_dueno = entrar(cliente, dueno.email)

    respuesta = cliente.post(
        "/admin/accounts",
        json={"name": "Colado", "email": "colado@solve.cl", "password": "clave-larga-de-colado"},
        headers=con_token(token_dueno),
    )

    assert respuesta.status_code == 403
    assert cliente.post(
        "/admin/accounts",
        json={"name": "Colado", "email": "colado@solve.cl", "password": "clave-larga-de-colado"},
        headers={"X-Admin-Key": CLAVE_ADMIN},
    ).status_code == 401


def test_las_cuentas_de_solve_se_pueden_mirar(cliente, token_admin):
    lista = cliente.get("/admin/accounts", headers=con_token(token_admin))

    assert lista.status_code == 200
    assert [c["email"] for c in lista.json()["data"]] == ["vicente@solve.cl"]


def test_se_puede_dar_de_baja_a_un_admin(cliente, token_admin):
    otro = cliente.post(
        "/admin/accounts",
        json={"name": "Martin", "email": "martin@solve.cl", "password": "clave-larga-de-martin"},
        headers=con_token(token_admin),
    ).json()["data"]

    apagado = cliente.patch(
        f"/admin/accounts/{otro['id']}",
        json={"active": False},
        headers=con_token(token_admin),
    )

    assert apagado.status_code == 200
    assert cliente.post(
        "/auth/login",
        json={"email": "martin@solve.cl", "password": "clave-larga-de-martin"},
    ).status_code == 401


def test_el_panel_nunca_se_queda_sin_ninguna_cuenta_activa(cliente, token_admin, sesion):
    """Si las dos cuentas se apagaran, el panel quedaria cerrado para todos y la unica
    salida seria volver a la consola del servidor.

    Basta con prohibir apagarse a si mismo: quien hace la peticion es un admin activo,
    asi que apagando al otro siempre queda el, y apagandose a el mismo choca con esto.
    """
    yo = sesion.scalar(select(User).where(User.email == "vicente@solve.cl"))
    otro = cliente.post(
        "/admin/accounts",
        json={"name": "Martin", "email": "martin@solve.cl", "password": "clave-larga-de-martin"},
        headers=con_token(token_admin),
    ).json()["data"]

    # Apagar al otro se puede: yo sigo activo.
    assert cliente.patch(
        f"/admin/accounts/{otro['id']}",
        json={"active": False},
        headers=con_token(token_admin),
    ).status_code == 200

    # Apagarme a mi, no.
    respuesta = cliente.patch(
        f"/admin/accounts/{yo.id}", json={"active": False}, headers=con_token(token_admin)
    )
    assert respuesta.status_code == 409
    assert entrar(cliente, "vicente@solve.cl", clave=CLAVE_DEL_ADMIN)
```

- [ ] **Step 2: Correr y verificar que fallan**

Run: `.venv/Scripts/python.exe -m pytest tests/test_admin.py -k "cuenta or admin_crea or solve" -v`
Expected: FAIL con 404/405.

- [ ] **Step 3: Ajustar los esquemas**

En `app/schemas/admin.py`, dejar `CuentaAdminEntrada` con el minimo de la plataforma y agregar la edicion:

```python
from app.services.altas import LARGO_MINIMO_DE_CLAVE_ADMIN


class CuentaAdminEntrada(Esquema):
    """Una cuenta de Solve. No pertenece a ningun taller de verdad."""

    name: Texto = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=LARGO_MINIMO_DE_CLAVE_ADMIN, max_length=200)


class CuentaAdminEdicion(Esquema):
    name: Texto | None = Field(default=None, min_length=2, max_length=120)
    active: bool | None = None


class UsuarioAdminSalida(Esquema):
    id: str
    name: str
    email: str
    role: str
    active: bool
```

**Cuidado:** `UsuarioAdminSalida` gana el campo `active`; ya se usa en `cambiar_clave_del_dueno` y ahi tambien saldra, que es correcto.

- [ ] **Step 4: Escribir los endpoints**

Al final de `app/routes/admin.py`:

```python
@router.post("/accounts", status_code=status.HTTP_201_CREATED)
def crear_cuenta_de_admin(
    datos: CuentaAdminEntrada,
    admin: User = Depends(solo_admin_plataforma),
    sesion: Session = Depends(obtener_sesion),
):
    """La segunda cuenta de Solve y las que sigan.

    No resucita la ruta que se borro: aquella pedia una llave que viajaba por internet y
    creaba la cuenta mas poderosa del sistema sin dejar rastro de quien lo hizo. Esta
    exige una sesion de administrador, asi que hay una persona identificable detras y
    queda anotada. La primera cuenta sigue naciendo en la consola del servidor.
    """
    try:
        nuevo = crear_admin(sesion, datos.name, datos.email, datos.password)
    except NoSePudoCrear as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)
        ) from None

    sesion.flush()
    _anotar(sesion, admin, ACCION_CUENTA_ADMIN_CREADA, usuario_id=nuevo.id)
    sesion.commit()

    return {"data": UsuarioAdminSalida.model_validate(nuevo).model_dump(by_alias=True)}


@router.get("/accounts", dependencies=[Depends(solo_admin_plataforma)])
def listar_cuentas_de_admin(sesion: Session = Depends(obtener_sesion)):
    """Quien tiene las llaves del panel. Se mira antes de crear otra o apagar una."""
    cuentas = sesion.scalars(
        select(User)
        .where(User.role == ROL_ADMIN_PLATAFORMA)
        .order_by(User.created_at)
    ).all()

    return {
        "data": [
            UsuarioAdminSalida.model_validate(cuenta).model_dump(by_alias=True)
            for cuenta in cuentas
        ]
    }


@router.patch("/accounts/{cuenta_id}")
def editar_cuenta_de_admin(
    cuenta_id: str,
    datos: CuentaAdminEdicion,
    admin: User = Depends(solo_admin_plataforma),
    sesion: Session = Depends(obtener_sesion),
):
    """Apagar o renombrar una cuenta de Solve.

    Nunca la ultima activa, y nunca la propia: quedarse sin ninguna cuenta de plataforma
    deja el panel cerrado para todos, y la unica salida seria volver a la consola del
    servidor.
    """
    cuenta = sesion.scalar(
        select(User).where(User.id == cuenta_id, User.role == ROL_ADMIN_PLATAFORMA)
    )
    if cuenta is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cuenta no encontrada")

    cambios = datos.model_dump(exclude_unset=True)
    # Igual que con el equipo del taller: quien pide esto es un admin activo, asi que
    # apagando a otro siempre queda al menos uno. Prohibir apagarse a si mismo es lo
    # unico que hace falta para que el panel no quede cerrado para todos.
    if cambios.get("active") is False and cuenta.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No puedes desactivar tu propia cuenta",
        )

    for campo, valor in cambios.items():
        if valor is not None:
            setattr(cuenta, campo, valor)
    _anotar(sesion, admin, ACCION_CUENTA_ADMIN_EDITADA, usuario_id=cuenta.id)
    sesion.commit()

    return {"data": UsuarioAdminSalida.model_validate(cuenta).model_dump(by_alias=True)}
```

Agregar los imports: `ROL_ADMIN_PLATAFORMA`, `ACCION_CUENTA_ADMIN_CREADA`, `ACCION_CUENTA_ADMIN_EDITADA` desde `app.models`; `CuentaAdminEdicion`, `CuentaAdminEntrada` desde `app.schemas.admin`; `NoSePudoCrear`, `crear_admin` desde `app.services.altas`.

Actualizar el docstring del modulo `app/routes/admin.py`: ya no es cierto que "las cuentas de admin NO se crean por aca". Dejarlo asi:

```python
"""El panel de Solve: dar de alta talleres, mirarlos, corregirlos y suspenderlos.

Nada de aca toca los datos de un taller. Un admin de plataforma no ve ordenes, clientes
ni vehiculos: esos endpoints siguen filtrando por el taller del token, sin excepcion.

La PRIMERA cuenta de administracion se crea con `scripts/crear_admin.py`, en la consola
del servidor. Las siguientes se crean aca, pero con la sesion de un admin que ya entro:
lo que se borro fue la ruta que las creaba con una llave suelta, sin nadie identificable
detras. Todo lo que hace el admin queda registrado en `admin_audit`.
"""
```

- [ ] **Step 5: Correr los tests**

Run: `.venv/Scripts/python.exe -m pytest tests/test_admin.py -v`
Expected: PASS

Run: `.venv/Scripts/python.exe -m pytest`
Expected: todo verde.

- [ ] **Step 6: Commit**

```bash
git add app/schemas/admin.py app/routes/admin.py tests/test_admin.py
git commit -m "Crear, mirar y dar de baja las cuentas de Solve desde el panel"
```

---

### Task 10: Cerrar el circulo y dejar la documentacion al dia

**Files:**
- Modify: `tests/test_admin.py`
- Modify: `README.md`
- Modify: `frontend/BACKEND.txt`
- Modify: `openapi.json` (se regenera)

- [ ] **Step 1: Escribir la prueba de circuito cerrado**

```python
def test_suspender_el_taller_bota_al_mecanico_que_estaba_trabajando(cliente, token_admin):
    """La prueba que junta todo: el mecanico esta con la sesion abierta, Solve suspende
    su taller, y el mecanico se cae en el siguiente click sin esperar a que venza nada."""
    taller_id = alta_de_taller(cliente, token_admin).json()["data"]["workshop"]["id"]
    cliente.post(
        f"/admin/workshops/{taller_id}/users",
        json={"name": "Pedro", "email": "pedro@sancristobal.cl", "password": "clave-larga-1"},
        headers=con_token(token_admin),
    )
    token_mecanico = entrar(cliente, "pedro@sancristobal.cl", clave="clave-larga-1")
    assert cliente.get("/orders", headers=con_token(token_mecanico)).status_code == 200

    cliente.patch(
        f"/admin/workshops/{taller_id}",
        json={"active": False},
        headers=con_token(token_admin),
    )

    assert cliente.get("/orders", headers=con_token(token_mecanico)).status_code == 401

    # Y al reactivar vuelve a trabajar con todo donde estaba.
    cliente.patch(
        f"/admin/workshops/{taller_id}",
        json={"active": True},
        headers=con_token(token_admin),
    )
    assert cliente.get(
        "/orders", headers=con_token(entrar(cliente, "pedro@sancristobal.cl", clave="clave-larga-1"))
    ).status_code == 200
```

- [ ] **Step 2: Correr la suite entera**

Run: `.venv/Scripts/python.exe -m pytest`
Expected: todo verde.

- [ ] **Step 3: Regenerar el contrato para Martin**

Run: `.venv/Scripts/python.exe scripts/exportar_openapi.py`
Expected: `openapi.json` actualizado con `/users` y las rutas nuevas de `/admin`.

- [ ] **Step 4: Actualizar el README**

En la tabla de fases de `README.md`, agregar una fila:

```markdown
| F7 | Equipo del taller, suspension y baja de talleres | ✅ |
```

Y en la seccion "Para Martin", agregar despues de las convenciones:

```markdown
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
```

- [ ] **Step 5: Actualizar `frontend/BACKEND.txt`**

Leer el archivo primero: es el resumen que lee Martin y tiene su propio formato. Respetarlo y agregar estas rutas al listado que ya exista ahi:

```
GET    /users                      lista el equipo del taller (solo el dueno)
POST   /users                      crea un mecanico          (solo el dueno)
PATCH  /users/:id                  { name?, active? }        (solo el dueno)
POST   /users/:id/password         { password }              (solo el dueno)

PATCH  /admin/workshops/:id        { name?, phone?, active? }  active:false suspende
DELETE /admin/workshops/:id        da de baja (204). No borra datos
POST   /admin/workshops/:id/restore   revive un taller dado de baja
GET    /admin/workshops?archived=true  solo los dados de baja
GET    /admin/workshops/:id/users  el equipo de un taller
POST   /admin/workshops/:id/users  alta de respaldo { name, email, password, role? }
POST   /admin/accounts             otra cuenta de Solve (clave de 12+)
GET    /admin/accounts             las cuentas de Solve
PATCH  /admin/accounts/:id         { name?, active? }

Notas:
- Apagar a alguien no lo borra: sigue en GET /users con active:false.
- Suspender un taller deja fuera a su gente en el siguiente request, no al vencer el token.
- Un dueno que pida por alguien de otro taller recibe 404, no 403.
```

- [ ] **Step 6: Commit**

```bash
git add tests/test_admin.py README.md frontend/BACKEND.txt openapi.json
git commit -m "Cerrar el circulo: suspender un taller bota a quien estaba trabajando"
```

---

## Despues del plan: las dos cuentas

No es codigo y no se hace desde aca. Una vez desplegado, en la consola del servidor:

```bash
python scripts/crear_admin.py --nombre "Vicente" --email <correo> --password <clave de 12+>
```

La de Martin se crea despues desde el panel con `POST /admin/accounts`, ya con la sesion
de la primera, y queda anotada en `admin_audit`. Antes conviene mirar
`GET /admin/accounts` por si ya hay alguna creada en Railway.
