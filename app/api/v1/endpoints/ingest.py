"""
Ingest endpoint — called by the ESP32 collar every few seconds.
Kept intentionally thin; all logic lives in TelemetryService.
"""

from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_db
from app.schemas.schemas import TelemetryIngest
from app.services.telemetry import TelemetryService

router = APIRouter(prefix="/ingest", tags=["Ingest"])


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def ingest_telemetry(
    payload: TelemetryIngest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Receive a telemetry reading from an ESP32 collar.
    Saves to MongoDB and queues behavior analysis asynchronously.
    """
    return await TelemetryService.ingest(payload, db, background_tasks)
