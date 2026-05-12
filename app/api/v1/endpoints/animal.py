from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_db
from app.models.sql import Animal
from app.schemas.schemas import AnimalCreate, AnimalRead

router = APIRouter(prefix="/animal", tags=["Animal"])


@router.get("", response_model=list[AnimalRead])
async def list_animals(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Animal).where(Animal.is_active == True).offset(skip).limit(limit)
    )
    return result.scalars().all()


@router.post("", response_model=AnimalRead, status_code=status.HTTP_201_CREATED)
async def create_animal(
    payload: AnimalCreate,
    db: AsyncSession = Depends(get_db),
):
    animal = Animal(**payload.model_dump())
    db.add(animal)
    await db.flush()
    await db.refresh(animal)
    return animal


@router.get("/{animal_id}", response_model=AnimalRead)
async def get_animal(animal_id: UUID, db: AsyncSession = Depends(get_db)):
    animal = await db.get(Animal, animal_id)
    if not animal:
        raise HTTPException(status_code=404, detail="Animal not found")
    return animal


@router.patch("/{animal_id}", response_model=AnimalRead)
async def update_animal(
    animal_id: UUID,
    payload: AnimalCreate,
    db: AsyncSession = Depends(get_db),
):
    animal = await db.get(Animal, animal_id)
    if not animal:
        raise HTTPException(status_code=404, detail="Animal not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(animal, field, value)
    await db.flush()
    await db.refresh(animal)
    return animal


@router.delete("/{animal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_animal(animal_id: UUID, db: AsyncSession = Depends(get_db)):
    animal = await db.get(Animal, animal_id)
    if not animal:
        raise HTTPException(status_code=404, detail="Animal not found")
    animal.is_active = False
    await db.flush()
