from uuid import UUID

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_db
from app.models.sql import User
from app.schemas.schemas import UserCreate, UserRead

router = APIRouter(prefix="/users", tags=["Users"])

# OBTENER TODOS LOS USUARIOS (solo para desarrollo, quitar luego)
@router.get("", response_model=list[UserRead])
async def list_Users(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).where(User.is_active == True).offset(skip).limit(limit)
    )
    return result.scalars().all()

# CREAR UN NUEVO USUARIO
@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(User).where(User.email == payload.email)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        name=payload.name,
        email=payload.email,
        hashed_password=bcrypt.hashpw(
            payload.password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8"),
        role=payload.role,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user

# OBTENER UN USUARIO POR ID
@router.get("/{user_id}", response_model=UserRead)
async def get_user(user_id: UUID, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# DESACTIVAR UN USUARIO (LOGICO)
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(user_id: UUID, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False
    await db.flush()

# ACTUALIZAR UN USUARIO
@router.put("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: UUID,
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    for key, value in payload.model_dump(exclude_unset=True).items():
        if key == "password":
            setattr(user, key, bcrypt.hashpw(
                value.encode("utf-8"),
                bcrypt.gensalt()
            ).decode("utf-8"))
        else:
            setattr(user, key, value)
    
    await db.flush()
    await db.refresh(user)
    return user
