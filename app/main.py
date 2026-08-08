from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.errores import registrar_manejadores
from app.routes import auth, clients, notifications, orders, statuses, vehicles

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
app.include_router(orders.router)
app.include_router(notifications.router)
app.include_router(statuses.router)


@app.get("/health")
def health():
    return {"data": {"status": "ok"}}
