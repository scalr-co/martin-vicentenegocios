#!/bin/sh
# Arranque en produccion: primero deja la base al dia, despues levanta la API.
#
# Las migraciones corren aca y no a mano porque un despliegue con la tabla nueva a medias
# es una API que responde 500 hasta que alguien se acuerde. Si fallan, el contenedor no
# levanta: mejor no arrancar que arrancar contra una base que no calza con el codigo.
set -e

echo "Aplicando migraciones..."
alembic upgrade head

# El hosting asigna el puerto por variable de entorno; en local no existe y usamos 8000.
PUERTO="${PORT:-8000}"

echo "Levantando la API en el puerto ${PUERTO}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PUERTO}"
