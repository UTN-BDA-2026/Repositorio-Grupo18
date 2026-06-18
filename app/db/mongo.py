from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings

_client: AsyncIOMotorClient | None = None


def get_mongo_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(settings.MONGO_URL)
    return _client


def get_mongo_db() -> AsyncIOMotorDatabase:
    return get_mongo_client()[settings.MONGO_DB]


async def close_mongo():
    global _client
    if _client is not None:
        _client.close()
        _client = None


# ── Collection helpers ────────────────────────────────────────────────────────

def telemetry_collection():
    """Raw GPS + accelerometer readings from collars."""
    return get_mongo_db()["telemetry"]


def behavior_snapshots_collection():
    """Aggregated behavior windows used for pgvector analysis."""
    return get_mongo_db()["behavior_snapshots"]
