"""Devices endpoints"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_db
from app.models.sql import Device
from app.schemas.schemas import DeviceCreate, DeviceRead

router = APIRouter(prefix="/devices", tags=["Devices"])
# OBTENER TODOS LOS DISPOSITIVOS
@router.get("", response_model=list[DeviceRead])
async def list_devices(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Device))
    return result.scalars().all()

# CREAR UN NUEVO DISPOSITIVO
@router.post("", response_model=DeviceRead, status_code=status.HTTP_201_CREATED)
async def register_device(payload: DeviceCreate, db: AsyncSession = Depends(get_db)):
    device = Device(**payload.model_dump())
    db.add(device)
    await db.flush()
    await db.refresh(device)
    return device

# OBTENER UN DISPOSITIVO POR ID
@router.get("/{device_id}", response_model=DeviceRead)
async def get_device(device_id: UUID, db: AsyncSession = Depends(get_db)):
    device = await db.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device

# OBTENER UN DISPOSITIVO POR HARDWARE ID
@router.get("/hardware/{hardware_id}", response_model=DeviceRead)
async def get_device_by_hardware_id(hardware_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Device).where(Device.hardware_id == hardware_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device

# ELIMINAR UN DISPOSITIVO
@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device(device_id: UUID, db: AsyncSession = Depends(get_db)):
    device = await db.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    await db.delete(device)
    await db.flush()

# ACTUALIZAR UN DISPOSITIVO
@router.patch("/{device_id}", response_model=DeviceRead)
async def update_device(
    device_id: UUID,
    payload: DeviceCreate,
    db: AsyncSession = Depends(get_db),
):
    device = await db.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(device, field, value)
    await db.flush()
    await db.refresh(device)
    return device
# OBTENER LOS DISPOSITIVOS POR USUARIO
@router.get("/user/{user_id}", response_model=list[DeviceRead])
async def get_devices_by_user(user_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Device).where(Device.user_id == user_id))
    return result.scalars().all()
