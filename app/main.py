from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.errores import registrar_manejadores
from app.routes import auth, clients, vehicles

app = FastAPI(title="TallerTrack API")

registrar_manejadores(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origenes_permitidos,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(clients.router)
app.include_router(vehicles.router)


@app.get("/health")
def health():
    return {"data": {"status": "ok"}}
