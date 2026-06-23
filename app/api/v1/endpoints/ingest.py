"""
Ingest endpoint
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
    
    # Recibimos la telemetrÃ­a de un collar ESP32. Guardamos en MongoDB.
    return await TelemetryService.ingest(payload, db, background_tasks)
