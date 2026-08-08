# Desplegar en Railway

Para que la API deje de vivir en un computador y Martin pueda apuntarle el frontend.
Railway construye la imagen con el `Dockerfile` del repositorio y la vuelve a construir
sola en cada push a `main`.

## 1. Crear el proyecto

1. Entrar a <https://railway.app> con la cuenta de GitHub.
2. **New Project → Deploy from GitHub repo** y elegir `martin-vicentenegocios`.
3. Railway detecta el `Dockerfile` y empieza a construir. El primer intento va a fallar
   o quedar arriba sin base de datos: falta el paso 2.

## 2. Agregar Postgres

En el mismo proyecto: **New → Database → Add PostgreSQL**.

Railway crea la base y expone su URL como variable. En el servicio de la API hay que
apuntarle esa variable:

| Variable | Valor |
|---|---|
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` |

Se escribe con esas llaves: es una referencia, no un texto. Asi, si Railway rota la clave
de la base, la API se entera sola.

> Railway entrega la URL como `postgresql://...`. La aplicacion la traduce sola al driver
> que tiene instalado (psycopg 3); no hay que tocarla a mano.

## 3. Las demas variables

En el servicio de la API, pestana **Variables**:

| Variable | Valor | Para que |
|---|---|---|
| `ENTORNO` | `produccion` | Pone estrictas las validaciones de arranque |
| `JWT_SECRET` | una clave propia, larga | Firma las sesiones |
| `ADMIN_API_KEY` | otra clave propia | Permite dar de alta talleres |
| `FRONTEND_ORIGINS` | `http://localhost:3000` | Mientras el frontend corra en el computador de Martin |

Las dos claves se generan asi, cada una por separado:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

**No sirve inventarlas cortas**: con `ENTORNO=produccion` la aplicacion se niega a arrancar
si `JWT_SECRET` es la de desarrollo o tiene menos de 32 caracteres. Es a proposito: la de
desarrollo esta escrita en este repositorio publico y cualquiera podria fabricarse un token.

## 4. Publicar la URL

En **Settings → Networking → Generate Domain**. Queda algo como
`tallertrack-production.up.railway.app`.

Comprobar que respondio bien:

- `https://esa-url/health` tiene que devolver `{"data":{"status":"ok"}}`
- `https://esa-url/docs` muestra la lista de endpoints

Las migraciones corren solas al arrancar el contenedor, asi que las tablas ya estan.

## 5. Dar de alta el primer taller

El alta no es publica: se hace con la clave de administracion.

```bash
curl -X POST https://esa-url/auth/register \
  -H "Content-Type: application/json" \
  -H "X-Admin-Key: LA_ADMIN_API_KEY" \
  -d '{"workshopName":"Taller Los Alerces","workshopPhone":"56912345678",
       "ownerName":"Nombre del dueno","email":"dueno@taller.cl","password":"una clave larga"}'
```

Devuelve el taller, el usuario y un token listo para usar.

## 6. Avisarle a Martin

Necesita dos cosas: la URL base y que el token va en `Authorization: Bearer <token>`.

Cuando publique su frontend (Vercel, por ejemplo), hay que agregar su dominio a
`FRONTEND_ORIGINS`, separado por coma:

```
FRONTEND_ORIGINS=http://localhost:3000,https://tallertrack.vercel.app
```

Sin ese paso el navegador le bloquea todas las llamadas, aunque la API este perfecta.

## Si algo falla

| Sintoma | Que suele ser |
|---|---|
| El contenedor no levanta y el log habla de `JWT_SECRET` | La clave quedo corta o sigue siendo la de desarrollo |
| El log habla de `psycopg2` | La `DATABASE_URL` no llego; revisar que la referencia `${{Postgres.DATABASE_URL}}` este bien escrita |
| El frontend recibe error de CORS | Falta su dominio en `FRONTEND_ORIGINS` |
| `/health` responde pero todo lo demas da 500 | Las migraciones fallaron; mirar el log del arranque |
