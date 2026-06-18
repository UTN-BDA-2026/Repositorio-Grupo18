from fastapi import APIRouter
from app.api.v1.endpoints import (
    users,
    animal,
    device,
    telemetry,
    ingest,
    ground,
)

api_router = APIRouter(prefix="/api/v1")

# RUTAS DE CADA MODELO
api_router.include_router(ingest.router)
api_router.include_router(users.router)
api_router.include_router(animal.router)
api_router.include_router(device.router)
api_router.include_router(telemetry.router)
api_router.include_router(ground.router)
