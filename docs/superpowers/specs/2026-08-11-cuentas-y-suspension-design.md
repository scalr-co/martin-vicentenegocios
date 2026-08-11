# Cuentas: equipo del taller y suspension de talleres

Fecha: 2026-08-11
Estado: aprobado. Listo para escribir el plan de implementacion.
Alcance: backend. El frontend queda para Martin, contra `/docs`.
Base: rama `auditoria-backend`, commit `cd267e4` mas el trabajo de sesiones sin commitear.

## El problema

Hoy un taller se da de alta con su dueno y no hay forma de agregarle un mecanico: no
existe ninguna ruta de usuarios. Un taller que deja de pagar no se puede cortar, porque
aunque `Workshop.active` existe y el login lo respeta, ningun endpoint lo cambia. Y la
segunda cuenta de administracion no se puede crear desde el panel, aunque
`scripts/crear_admin.py:13` promete que "las cuentas siguientes las crea un admin ya
logueado".

Dicho corto: el sistema sabe negar el acceso, pero nadie puede apretar el interruptor.

## Lo que ya existe y no hay que rehacer

| Pieza | Donde | Estado |
|---|---|---|
| Rol `platform_admin` | `app/models/user.py` | ✅ |
| Roles `owner` y `mechanic` | `app/models/user.py` | ✅ |
| `solo_admin_plataforma` | `app/security/dependencias.py` | ✅ |
| `solo_dueno` | `app/security/dependencias.py` | escrita, **sin usar** |
| `User.active`, `Workshop.active` | modelos | ✅ campos |
| Login y `usuario_actual` respetan `active` | `auth.py`, `dependencias.py` | ✅ |
| Primera cuenta de Solve, por consola | `scripts/crear_admin.py` | ✅ |
| Alta de talleres, listado, clave del dueno | `app/routes/admin.py` | ✅ |
| Registro de auditoria del admin | `app/models/admin_audit.py`, `_anotar` | ✅ |
| Cierre de sesiones por `token_version` | `user.py`, `dependencias.py`, `/auth/logout-all` | ✅ |

Falta: crear usuarios de taller, desactivarlos, suspender o dar de baja un taller, y
crear la segunda cuenta de administracion desde el panel.

## Decisiones tomadas

1. **Los mecanicos los crea el dueno de su taller.** Solve puede hacerlo tambien, como
   respaldo, cuando el dueno se pierda o pida ayuda. Solve no queda de portero.
2. **Dos niveles de corte, cada uno en su lugar.** Solve suspende o da de baja talleres
   completos. El dueno desactiva a las personas de su propio taller.
3. **Nada se borra nunca desde la API.** Se sigue la convencion del commit `dd8e6d1`
   ("Archivar clientes y ordenes en vez de borrarlos"). El taller que deja de pagar
   necesita no poder entrar, no perder sus datos: si vuelve en dos meses se reactiva y
   encuentra sus ordenes, sus clientes y su historial por patente intactos.
4. **Todo lo que haga el admin queda anotado en `admin_audit`.** Decidido primero que no,
   revertido al encontrar que la tabla ya existe con ese proposito exacto: dejar dicho
   quien dejo a alguien fuera y cuando. Suspender un taller entero es mas drastico que
   cambiarle la clave al dueno, que ya se anota. Cuesta constantes nuevas, nada mas.

## Los tres estados de un taller

Dos campos, sin enum y sin tocar el camino de autenticacion:

| Estado | `active` | `deleted_at` | Que significa |
|---|---|---|---|
| Activo | `True` | `NULL` | opera normal |
| Suspendido | `False` | `NULL` | dejo de pagar, va a volver. Sale en el panel |
| Dado de baja | `False` | fecha | se fue. Oculto salvo `?archived=true` |

`active` sigue siendo **la unica puerta de acceso**: es lo que ya preguntan `login` y
`usuario_actual`, y esa linea no se modifica. `deleted_at` solo decide si el taller
aparece en la lista del panel. El contrato con el frontend tampoco cambia:
`WorkshopSalida.active` significa exactamente lo mismo que hoy.

Se descarto una columna `status` con los tres valores escritos: seria mas explicita de
leer, pero obliga a tocar `usuario_actual` y `login` —el codigo mas delicado del
sistema, y que ademas acaba de cambiar por `token_version`—, a migrar las filas que ya
estan en Railway y a redefinir `active` en una respuesta que el frontend ya consume.

## Nivel taller: `app/routes/users.py` (nuevo)

Prefijo `/users`. Todo detras de `solo_dueno`, que se estrena aca.

| Endpoint | Que hace | Respuesta |
|---|---|---|
| `POST /users` | crea un mecanico en el taller del token | 201 |
| `GET /users` | lista el equipo del taller | 200 |
| `PATCH /users/{id}` | cambia `name` y/o `active` | 200 |
| `POST /users/{id}/password` | resetea la clave de un mecanico | 200 |

**Los usuarios no llevan `deleted_at`.** Un mecanico desactivado tiene que seguir visible
en la lista: el dueno necesita verlo apagado para poder reactivarlo, y su nombre sigue
colgando del historial de ordenes por `order_event.user_id`. Esconderlo seria peor que
mostrarlo. Consecuencia practica: **los usuarios no necesitan migracion**.

Desactivar y reactivar viven en el mismo `PATCH`, que es lo natural para un interruptor.
No se usa `DELETE` aca —a diferencia de clientes y ordenes— porque esto no es archivar.

### Esquemas

```python
# app/schemas/user.py (nuevo)

class UsuarioEntrada(Esquema):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=200)

class UsuarioEdicion(Esquema):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    active: bool | None = None

class UsuarioSalida(Esquema):
    id: str
    name: str
    email: EmailStr
    role: str
    active: bool
    created_at: datetime
```

`UsuarioSalida` agrega `active` y `created_at` a lo que hoy expone `UserSalida`, y sigue
sin `password_hash`, por la razon escrita en `app/schemas/auth.py`: lo que no se expone no
se puede filtrar. Para la clave nueva se reusa `ClaveNueva`, de `app/schemas/admin.py`.

## Nivel plataforma: ampliar `app/routes/admin.py`

Todo detras de `solo_admin_plataforma`.

| Endpoint | Que hace | Respuesta |
|---|---|---|
| `PATCH /admin/workshops/{id}` | **ya existe**; se agrega `active` a `TallerEdicion` para suspender y reactivar | 200 |
| `DELETE /admin/workshops/{id}` | dar de baja: escribe `deleted_at` y deja `active=False` | 204 |
| `POST /admin/workshops/{id}/restore` | revive un taller dado de baja | 200 |
| `GET /admin/workshops` | **ya existe**; acepta `?archived=true` | 200 |
| `POST /admin/workshops/{id}/users` | el respaldo: crea un usuario en cualquier taller | 201 |
| `GET /admin/workshops/{id}/users` | ve el equipo de cualquier taller | 200 |
| `POST /admin/accounts` | crea otra cuenta de Solve, **con sesion de admin** | 201 |
| `GET /admin/accounts` | lista las cuentas de Solve | 200 |
| `PATCH /admin/accounts/{id}` | cambia `name` y/o `active` de una cuenta de Solve | 200 |

`DELETE` que archiva y responde 204 es lo que ya hacen `app/routes/clients.py` y
`app/routes/orders.py`.

`GET /admin/workshops` por defecto oculta los dados de baja y **si muestra los
suspendidos**, con su bandera `active: false`: son justamente los que se van a reactivar,
esconderlos los volveria irrecuperables desde el panel.

El alta de respaldo (`POST /admin/workshops/{id}/users`) acepta `role` y permite crear un
`owner`, para el taller que perdio al suyo. El `POST /users` del dueno no: fuerza
`mechanic`.

### Sobre `POST /admin/accounts`

El commit `cd267e4` borro la ruta que creaba admins con `X-Admin-Key` suelta, y con razon:
esa llave viajaba por internet y creaba la cuenta mas poderosa del sistema sin dejar
registro de quien lo hizo. Esta ruta **no la resucita**. La diferencia es entera:

- exige una **sesion de administrador** (`solo_admin_plataforma`), no una llave;
- por lo tanto hay una persona identificable detras, y queda anotada en `admin_audit`;
- la llave raiz sigue viviendo solo en la consola del servidor, con
  `scripts/crear_admin.py`, para la primera cuenta.

Es exactamente lo que ese script promete en su docstring y todavia no existia. Reusa
`crear_admin()` de `scripts/crear_admin.py`, que ya valida correo repetido y exige **12
caracteres** de clave —no 8— porque es la cuenta con mas poder del sistema. Esa funcion se
mueve a `app/services/altas.py` para que el script y la ruta compartan una sola
implementacion; el script pasa a importarla.

### Idempotencia

- `DELETE` sobre un taller ya dado de baja responde 204 y no mueve la fecha original.
- `POST .../restore` sobre un taller que no estaba dado de baja responde 200 y lo deja
  activo. No es error pedir lo que ya se cumple: el frontend puede reintentar sin miedo,
  igual que con `POST /notifications/:id/sent`.

## Las guardas

Son el valor real de la feature. Sin ellas, un panel de administracion es una forma
comoda de romper la base.

1. **Un dueno solo alcanza su propio taller.** `PATCH /users/{id}` o
   `POST /users/{id}/password` sobre alguien de otro taller responde **404, no 403**. Un
   403 confirmaria que ese id existe. Mismo criterio que ya aplican clientes, vehiculos
   y ordenes.
2. **Nadie se desactiva a si mismo** → 409. Vale para el dueno y para el admin de Solve.
   Es el candado que deja a la persona fuera de su propia casa.
3. **Un taller no se queda sin dueno activo** → 409 al desactivar al ultimo `owner`
   activo. Si no, ese taller pierde la capacidad de administrar su equipo y depende de
   que Solve lo rescate.
4. **Solve no se queda sin administradores** → 409 al desactivar la ultima cuenta
   `platform_admin` activa, por `PATCH /admin/accounts/{id}`. Con dos cuentas, esta
   guarda es la que impide que una equivocacion los deje a los dos fuera del panel.
5. **El taller interno de Solve no se suspende ni se da de baja.** Ya lo cubre el filtro
   `internal.is_(False)` de `_taller_o_404`.
6. **El dueno crea mecanicos, no duenos.** `POST /users` fuerza `role=mechanic`.
7. **El correo es unico en todo el sistema** → 409. El chequeo que hoy esta escrito dos
   veces —dentro de `crear_taller_con_dueno` y dentro de `crear_admin`— se saca a una
   funcion compartida en `app/services/altas.py`, para que las cuatro puertas de alta
   validen igual y no se separen con el tiempo.

## Cerrar las sesiones abiertas: `token_version`

El trabajo de sesiones que entro en esta rama cambia una regla, y esta feature tiene que
respetarla en cada punto donde se le quita acceso a alguien:

| Situacion | Que hay que hacer |
|---|---|
| `POST /users/{id}/password` (el dueno resetea a un mecanico) | **subir `token_version`**, igual que ya hace `cambiar_clave_del_dueno`. Si no, quien tenga el token viejo sigue adentro hasta 12 horas con una clave que ya no sirve |
| `PATCH /users/{id}` con `active=false` | no hace falta: `usuario_actual` ya rechaza al usuario inactivo en su siguiente request |
| Suspender o dar de baja un taller | no hace falta: `usuario_actual` ya rechaza cuando `workshop.active` es falso |

Es decir: **el corte de acceso ya funciona solo**, porque `usuario_actual` va a la base en
cada request. `token_version` solo se toca donde cambia una clave.

Al reactivar, todo vuelve solo. Los usuarios conservan su `active` individual: suspender
el taller no los apaga uno por uno.

## Auditoria

Se agregan constantes a `app/models/admin_audit.py` y se llama a `_anotar` en cada accion
nueva del admin:

```
ACCION_TALLER_SUSPENDIDO      = "workshop_suspended"
ACCION_TALLER_REACTIVADO      = "workshop_reactivated"
ACCION_TALLER_DADO_DE_BAJA    = "workshop_archived"
ACCION_TALLER_RESTAURADO      = "workshop_restored"
ACCION_USUARIO_CREADO         = "user_created"
ACCION_CUENTA_ADMIN_CREADA    = "admin_created"
ACCION_CUENTA_ADMIN_EDITADA   = "admin_updated"
```

Lo que hace el dueno dentro de su propio taller **no** se anota: `admin_audit` existe para
responder "quien de Solve entro a que taller", no para vigilar a los clientes.

## Limpieza incluida

`taller_interno` esta escrita dos veces —`app/services/altas.py` y dentro de
`app/routes/admin.py`— y las copias ya se separaron: una crea el taller interno con
telefono `56900000000` y la otra con `000000000`, que ni siquiera pasaria el validador de
telefonos chilenos del propio repositorio. Se borra la copia de `admin.py` y se importa la
de `altas.py`.

Es codigo que esta feature toca igual, y ya se dio vuelta una vez.

## Migracion

Una sola columna:

```
workshops.deleted_at  DateTime(timezone=True), nullable, default None
```

Misma forma que `clients.deleted_at`. Se genera con `alembic revision --autogenerate`, y
va **encima** de `f2a9c4d8e1b3_version_de_sesion`. Los talleres que ya viven en Railway
quedan en `NULL`, es decir activos, que es lo correcto.

Los usuarios no cambian de forma: no hay migracion para ellos.

## Tests

Sobre los 214 que ya existen, mas los de sesiones.

**`tests/test_users.py`** (nuevo)
- el dueno crea un mecanico y el mecanico puede entrar
- el dueno lista su equipo y ve a los desactivados, apagados
- desactivar y reactivar por `PATCH`
- resetear la clave de un mecanico: la vieja deja de servir, la nueva sirve, **y el token
  que tenia antes deja de servir** (`token_version`)
- un `mechanic` recibe 403 en todo `/users`
- **aislamiento**: el dueno del taller A recibe 404 al tocar a alguien del taller B
- una guarda por prueba: auto-desactivarse, ultimo dueno activo, correo repetido, y que
  `POST /users` no deja crear un `owner`

**`tests/test_admin.py`** (ampliar)
- suspender, reactivar, dar de baja, restaurar
- `GET /admin/workshops` oculta los dados de baja y muestra los suspendidos;
  `?archived=true` los trae
- alta de respaldo y listado del equipo de cualquier taller
- crear, listar y editar cuentas de Solve; la clave de admin exige 12 caracteres
- un `mechanic` y un `owner` reciben 403 en todo `/admin`
- no se puede suspender ni dar de baja el taller interno
- no se puede desactivar la ultima cuenta de plataforma, ni desactivarse a si mismo
- `DELETE` repetido no mueve la fecha de baja; `restore` sobre un taller activo no falla
- cada accion nueva deja su fila en `admin_audit`, con el admin correcto como actor

**La prueba que cierra el circulo**
- un mecanico con sesion abierta, Solve suspende su taller, su siguiente request es 401

## Procedimiento operativo: las dos cuentas

La primera cuenta nace en la consola del servidor, nunca por HTTP:

```bash
python scripts/crear_admin.py --nombre "Vicente" --email ... --password ...
```

La segunda —la de Martin— se crea desde el panel con `POST /admin/accounts`, ya con la
sesion de la primera, y queda anotada en `admin_audit` con nombre y apellido. Conviene
revisar antes con `GET /admin/accounts` si ya hay alguna creada en Railway.

## Fuera de alcance

- Pantallas en el frontend. Martin las arma contra `/docs`, que se genera solo.
- Borrado real de datos. Ningun endpoint borra filas.
- Que un usuario cambie su propia contrasena sabiendo la actual. Lo que entra aca es el
  reseteo hecho por el dueno o por Solve.
- Endpoint para leer `admin_audit`. Se escribe, todavia no se lee por HTTP.
- Invitaciones por correo. El dueno crea la cuenta con una clave y se la pasa a su
  mecanico como quiera.
