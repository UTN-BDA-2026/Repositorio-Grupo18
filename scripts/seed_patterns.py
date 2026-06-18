"""
seed_patterns.py
────────────────
Populates the behavior_patterns table with synthetic reference vectors.

In a real project these vectors would come from labelled field data.
For the faculty project, we simulate plausible feature distributions
for each behavioral state and insert them as reference embeddings.

Usage:
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

# (label, description, mean_vector_hint)
# The hint is just the mean; we add small Gaussian noise to simulate
# natural variation between animals.
PATTERNS = [
    (
        "healthy_grazing",
        "Normal grazing behavior: slow rhythmic head movements, low acceleration variance.",
        np.array([0.1, 0.05, 0.2] * (DIM // 3) + [0.1] * (DIM % 3)),
    ),
    (
        "healthy_resting",
        "Animal lying down or standing still. Very low accelerometer activity.",
        np.zeros(DIM) + 0.02,
    ),
    (
        "healthy_walking",
        "Normal locomotion between grazing areas.",
        np.array([0.5, 0.1, 0.6] * (DIM // 3) + [0.3] * (DIM % 3)),
    ),
    (
        "pre_calving",
        "Restlessness before labor: frequent posture changes, increased movement variance.",
        np.array([0.8, 0.7, 0.9] * (DIM // 3) + [0.8] * (DIM % 3)),
    ),
    (
        "illness_lethargy",
        "Sick animal: prolonged inactivity, abnormal low movement even at feeding time.",
        np.zeros(DIM) + 0.01,
    ),
    (
        "lameness",
        "Irregular gait detected via asymmetric acceleration peaks across axes.",
        np.array([0.9, 0.2, 0.3] * (DIM // 3) + [0.5] * (DIM % 3)),
    ),
]


def _make_vector(base: np.ndarray, noise_scale: float = 0.03) -> list[float]:
    vec = base + np.random.normal(0, noise_scale, size=DIM)
    # L2-normalize so cosine similarity makes sense
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec /= norm
    return vec[:DIM].tolist()


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # Clear existing patterns
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
