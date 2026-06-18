"""Devices endpoints"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_db
from app.models.sql import Device
from app.schemas.schemas import DeviceCreate, DeviceRead

router = APIRouter(prefix="/devices", tags=["Devices"])


@router.get("", response_model=list[DeviceRead])
async def list_devices(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Device))
    return result.scalars().all()


@router.post("", response_model=DeviceRead, status_code=status.HTTP_201_CREATED)
async def register_device(payload: DeviceCreate, db: AsyncSession = Depends(get_db)):
    device = Device(**payload.model_dump())
    db.add(device)
    await db.flush()
    await db.refresh(device)
    return device


@router.get("/{device_id}", response_model=DeviceRead)
async def get_device(device_id: UUID, db: AsyncSession = Depends(get_db)):
    device = await db.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device
