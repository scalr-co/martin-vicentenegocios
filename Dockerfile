FROM python:3.12-slim

WORKDIR /srv

# Las dependencias primero: si no cambian, Docker reutiliza esta capa y el build es rapido.
COPY pyproject.toml ./
RUN pip install --no-cache-dir .

COPY app ./app

# Las migraciones viajan con la imagen: al desplegar hay que poder crear o actualizar
# las tablas, y sin estos archivos el contenedor no sabria como.
COPY alembic ./alembic
COPY alembic.ini ./

# La primera cuenta de administracion se crea desde la consola del servidor, asi que el
# script tiene que estar DENTRO de la imagen. Sin esto, el unico camino documentado para
# estrenar el panel no existe alla. No queda expuesto: nada de scripts/ se sirve por HTTP.
COPY scripts ./scripts

COPY docker/arrancar.sh ./docker/arrancar.sh
RUN chmod +x ./docker/arrancar.sh

# En local es 8000; en Railway y compania el puerto lo asigna el hosting por $PORT.
EXPOSE 8000

CMD ["./docker/arrancar.sh"]
