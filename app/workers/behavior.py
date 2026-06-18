"""
BehaviorWorker
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
            float(np.sqrt(np.mean(arr ** 2))),  # RMS energy
        ]
        fft_magnitudes = np.abs(np.fft.rfft(arr))
        top3_idx = np.argsort(fft_magnitudes)[-3:][::-1]
        features += fft_magnitudes[top3_idx].tolist()

    # pad to BEHAVIOR_VECTOR_DIM
    padded = np.zeros(settings.BEHAVIOR_VECTOR_DIM, dtype=np.float32)
    n = min(len(features), settings.BEHAVIOR_VECTOR_DIM)
    padded[:n] = features[:n]
    return padded


async def analyze_behavior_window(animal_id: str, hardware_id: str) -> None:
    """
    Entry point called by BackgroundTasks.
    Fetches the last WINDOW_SIZE readings and runs pgvector similarity search.
    """
    # ── 1. Fetch readings from MongoDB ────────────────────────────────────────
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

    # ── 2. Extract feature vector ─────────────────────────────────────────────
    vector = _extract_features(readings)

    # ── 3. pgvector cosine similarity search ──────────────────────────────────
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
    Uses pgvector's <=> (cosine distance) operator to find the most similar
    reference pattern. If the similarity is above the threshold and the
    pattern is flagged as concerning, create a HealthAlert.
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

    if row is None:
        logger.info("No reference patterns found in DB. Skipping.")
        return

    similarity: float = float(row.similarity)
    label: str = row.label

    logger.info(
        "Animal %s → best match: '%s' (similarity=%.3f)",
        animal_id, label, similarity,
    )

    # Only alert if similarity is high AND the label is NOT "healthy_*"
    is_concerning = not label.startswith("healthy")
    if similarity >= settings.ALERT_SIMILARITY_THRESHOLD and is_concerning:
        alert = HealthAlert(
            animal_id=uuid.UUID(animal_id),
            alert_type="behavior",
            pattern_label=label,
            similarity_score=similarity,
            message=(
                f"Behavior pattern '{label}' detected with "
                f"{similarity * 100:.1f}% confidence."
            ),
        )
        db.add(alert)
        await db.commit()
        logger.warning(
            "🚨 Alert created for animal %s — pattern: %s", animal_id, label
        )
