from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_db
from app.models.sql import Livestock
from app.schemas.schemas import OperatorBase, OperatorCreate, OperatorRead

router = APIRouter(prefix="/operators", tags=["Operators"])


# GET
@router.get("", response_model=list[OperatorRead])
async def read_operators(
    db: AsyncSession = Depends(get_db),
) -> list[OperatorRead]:
    statement = select(Livestock)
    result = await db.execute(statement)
    return result.scalars().all()

# POST
@router.post("", response_model=OperatorRead, status_code=status.HTTP_201_CREATED)
async def create_operator(
    payload: OperatorCreate,
    db: AsyncSession = Depends(get_db),
):
    db_operator = Operator(**payload.model_dump())
    db.add(db_operator)
    await db.commit()
    await db.refresh(db_operator)
    return db_operator


# GET BY ID

@router.get("/{operator_id}", response_model=OperatorRead)
async def get_operator(operator_id: UUID, db: AsyncSession = Depends(get_db)):
    operator = await db.get(OperatorBase, operator_id)
    if not operator:
        raise HTTPException(status_code=404, detail="Operator not found")
    return animal


# DELETE
@router.delete("/{operator_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_operator(operator_id: UUID, db: AsyncSession = Depends(get_db)):
    operator = await db.get(OperatorBase, operator_id)
    if not operator:
        raise HTTPException(status_code=404, detail="Operator not found")
    await db.delete(operator)
    await db.commit()


