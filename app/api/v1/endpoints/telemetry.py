"""Telemetry endpoint """
from fastapi import APIRouter, Query
from app.services.telemetry import TelemetryService

router = APIRouter(prefix="/telemetry", tags=["Telemetry"])


@router.get("/{hardware_id}")
async def get_telemetry(
    hardware_id: str,
    limit: int = Query(default=100, le=1000),
):
    """retornar las ultimas lecturas de un collar"""
    return await TelemetryService.get_recent(hardware_id, limit)
