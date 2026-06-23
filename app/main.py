from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.mongo import close_mongo, get_mongo_db
from app.db.postgres import engine
from app.models.sql import Base

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Crear extensión pgvector y tablas
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Tablas PostgreSQL creadas/verificadas")

    # Ejecutar índices statement por statement
    try:
        with open("scripts/create_index.sql", "r") as f:
            raw = f.read()

        # Separar por ; y filtrar líneas vacías y comentarios
        statements = [
            s.strip() for s in raw.split(";")
            if s.strip() and not s.strip().startswith("--")
        ]

        async with engine.begin() as conn:
            for stmt in statements:
                await conn.execute(text(stmt))
                logger.info(f"Índice creado: {stmt[:60]}...")

    except FileNotFoundError:
        logger.warning("scripts/create_index.sql no encontrado, omitiendo índices")
    except Exception as e:
        logger.error(f"Error creando índices: {e}")

    # MongoDB: índice de telemetría
    db = get_mongo_db()
    await db["telemetry"].create_index(
        [("device_hardware_id", 1), ("timestamp", -1)]
    )
    logger.info("Índice MongoDB creado/verificado")

    yield

    await close_mongo()
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",   # para desarrollo local
        # luego nos queda agregar dominio de producción ej: https://smartfarming.com
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.get("/")
def read_root():
    return {"APP": "SMART FARMING 🐮"}

# Incluir rutas de la API
app.include_router(api_router)
