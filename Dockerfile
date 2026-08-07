FROM python:3.12-slim

WORKDIR /srv

# Las dependencias primero: si no cambian, Docker reutiliza esta capa y el build es rapido.
COPY pyproject.toml ./
RUN pip install --no-cache-dir .

COPY app ./app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
