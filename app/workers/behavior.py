"""
PATRONES DE COMPORTAMIENTO 
"""

import logging
import uuid
from typing import Optional

import numpy as np
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.mongo import telemetry_collection
from app.db.postgres import AsyncSessionLocal
from app.models.sql import BehaviorPattern, HealthAlert

logger = logging.getLogger(__name__)

WINDOW_SIZE = 30

def _extract_features(readings: list[dict]) -> np.ndarray:
    axes = {
        "x": np.array([r["accel"]["x"] for r in readings]),
        "y": np.array([r["accel"]["y"] for r in readings]),
        "z": np.array([r["accel"]["z"] for r in readings]),
    }

    features: list[float] = []
    for arr in axes.values():
        features += [
            float(np.mean(arr)),
            float(np.std(arr)),
            float(np.min(arr)),
            float(np.max(arr)),
            float(np.sqrt(np.mean(arr ** 2))), 
        ]
        fft_magnitudes = np.abs(np.fft.rfft(arr))
        top3_idx = np.argsort(fft_magnitudes)[-3:][::-1]
        features += fft_magnitudes[top3_idx].tolist()

    # Truncar o rellenar con ceros para que el vector tenga la longitud esperada
    padded = np.zeros(settings.BEHAVIOR_VECTOR_DIM, dtype=np.float32)
    n = min(len(features), settings.BEHAVIOR_VECTOR_DIM)
    padded[:n] = features[:n]
    return padded


async def analyze_behavior_window(animal_id: str, hardware_id: str) -> None:
    # Obtene los últimos 30 registros de telemetría del collar desde MongoDB
    cursor = (
        telemetry_collection()
        .find({"device_hardware_id": hardware_id})
        .sort("timestamp", -1)
        .limit(WINDOW_SIZE)
    )
    readings = await cursor.to_list(length=WINDOW_SIZE)

    if len(readings) < WINDOW_SIZE:
        logger.debug("Not enough readings yet for animal %s", animal_id)
        return

    # Extraer características del vector de comportamiento a partir de los datos de acelerómetro
    vector = _extract_features(readings)

    # Buscar el patrón de comportamiento más similar en la base de datos Postgres y crear una alerta si es necesario
    async with AsyncSessionLocal() as db:
        try:
            await _run_similarity_check(db, animal_id, vector)
        except Exception as exc:
            logger.error("Behavior analysis failed for animal %s: %s", animal_id, exc)
            await db.rollback()


async def _run_similarity_check(
    db: AsyncSession,
    animal_id: str,
    vector: np.ndarray,
) -> None:
    """
    Usamos el operador <=> de pgvector (distancia coseno) para encontrar el patrón de referencia más similar.
    Si la similitud está por encima del umbral y el patrón está marcado como preocupante, se crea una HealthAlert.
    """
    vector_literal = "[" + ",".join(str(v) for v in vector.tolist()) + "]"

    # cosine distance: 0 = identical, 1 = orthogonal
    # similarity = 1 - distance
    result = await db.execute(
        text(
            """
            SELECT id, label, description,
                   1 - (embedding <=> :vec ::vector) AS similarity
            FROM behavior_patterns
            ORDER BY embedding <=> :vec ::vector
            LIMIT 1
            """
        ),
        {"vec": vector_literal},
    )
    row = result.fetchone()
... (32 líneas restantes)
