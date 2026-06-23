"""
Creamos un conjunto de patrones de comportamiento de ejemplo para la base de datos.
Uso:
    python scripts/seed_patterns.py
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from sqlalchemy import delete

from app.core.config import settings
from app.db.postgres import AsyncSessionLocal, engine
from app.models.sql import Base, BehaviorPattern

DIM = settings.BEHAVIOR_VECTOR_DIM

# Definimos algunos patrones de comportamiento de ejemplo con descripciones y vectores base.
PATTERNS = [
    (
        "healthy_grazing",
        "Comportamiento normal de pastoreo: movimiento moderado con picos de actividad durante el día.",
        np.array([0.1, 0.05, 0.2] * (DIM // 3) + [0.1] * (DIM % 3)),
    ),
    (
        "healthy_resting",
        "Animal con bajo movimiento durante la noche, indicando descanso adecuado.",
        np.zeros(DIM) + 0.02,
    ),
    (
        "healthy_walking",
        "Movimiento constante con patrones regulares de aceleración, típico de un animal caminando por el campo.",
        np.array([0.5, 0.1, 0.6] * (DIM // 3) + [0.3] * (DIM % 3)),
    ),
    (
        "pre_calving",
        "Inquietud antes del parto: cambios frecuentes en la postura, aumento de la variación del movimiento.",
        np.array([0.8, 0.7, 0.9] * (DIM // 3) + [0.8] * (DIM % 3)),
    ),
    (
        "illness_lethargy",
        "Animal enfermo: inactividad prolongada, movimiento anormalmente bajo incluso durante el tiempo de alimentación.",
        np.zeros(DIM) + 0.01,
    ),
    (
        "lameness",
        "Marcha irregular detectada mediante picos de aceleración asimétricos a través de los ejes.",
        np.array([0.9, 0.2, 0.3] * (DIM // 3) + [0.5] * (DIM % 3)),
    ),
]


def _make_vector(base: np.ndarray, noise_scale: float = 0.03) -> list[float]:
    vec = base + np.random.normal(0, noise_scale, size=DIM)
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec /= norm
    return vec[:DIM].tolist()


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # Limpiamos la tabla de patrones de comportamiento antes de añadir nuevos datos.
        await db.execute(delete(BehaviorPattern))

        for label, description, base_vec in PATTERNS:
            pattern = BehaviorPattern(
                label=label,
                description=description,
                embedding=_make_vector(base_vec),
            )
            db.add(pattern)
            print(f"  ✓ Added pattern: {label}")

        await db.commit()
        print(f"\nSeeded {len(PATTERNS)} behavior patterns.")


if __name__ == "__main__":
    asyncio.run(seed())
