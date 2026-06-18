from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from sqlalchemy import text

from app.db.mongo import close_mongo, get_mongo_db
from app.db.postgres import engine
from app.models.sql import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Crear las tablas de PostgreSQL si no existen.
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        await conn.run_sync(Base.metadata.create_all)

    # Inicializar Mongo DB
    db = get_mongo_db()
    await db["telemetry"].create_index(
        [("device_hardware_id", 1), ("timestamp", -1)]
    )
    
    yield
    
    await close_mongo()
    await engine.dispose()

# Configurar la aplicacion FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Middleware para el acceso CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # quitar en produccion para solo permitir el frontend 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# Rutas de la API
@app.get("/")
def read_root():
    return {"APP": "SMART FARMING🐮"}

app.include_router(api_router)
