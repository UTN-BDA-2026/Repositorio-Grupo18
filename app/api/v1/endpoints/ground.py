"""
Ground endpoint
"""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_db
from app.models.sql import Ground
from app.schemas.schemas import GroundCreate, GroundRead
from shapely.geometry import Point, Polygon 


router = APIRouter(prefix="/ground", tags=["Ground"])


@router.get("", response_model=list[GroundRead])
async def list_grounds(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Ground))
    return result.scalars().all()


@router.post("", response_model=GroundRead, status_code=status.HTTP_201_CREATED)
async def create_ground(payload: GroundCreate, db: AsyncSession = Depends(get_db)):
    ground = Ground(**payload.model_dump())
    db.add(ground)
    await db.flush()
    await db.refresh(ground)
    return ground


@router.get("/{ground_id}", response_model=GroundRead)
async def get_ground(ground_id: UUID, db: AsyncSession = Depends(get_db)):
    ground = await db.get(Ground, ground_id)
    if not ground:
        raise HTTPException(status_code=404, detail="Ground not found")
    return ground


# Obtener por user id
@router.get("/user/{user_id}", response_model=list[GroundRead])
async def get_grounds_by_user(user_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Ground).where(Ground.users_id == user_id))
    return result.scalars().all()


# Validar posición (lat, lng) contra los corrales del usuario
@router.get("/validate-position/{user_id}")
async def validate_position(
    user_id: UUID, 
    lat: float, 
    lng: float, 
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint para el ESP32. Valida si una coordenada (lat, lng) está adentro
    de alguno de los corrales virtuales del usuario.
    """
    # 1. Buscamos todos los terrenos del usuario en Postgres
    result = await db.execute(select(Ground).where(Ground.users_id == user_id))
    grounds = result.scalars().all()
    
    if not grounds:
        # Si el usuario no tiene corrales, por seguridad asumimos que está "adentro" o tiramos ok
        return {"is_inside": True, "alert": False}

    # Creamos el punto geométrico de la ubicación actual de la vaca
    vaca_point = Point(lat, lng)

    # 2. Recorremos los corrales para ver si el punto cae adentro de al menos UNO
    for ground in grounds:
        if not ground.geofence:
            continue
        
        try:
            # Parseamos el string JSON que guardó el frontend a una lista de Python
            coords_list = json.loads(ground.geofence)
            
            # Formateamos los vértices para Shapely: (lat, lng)
            polygon_vertices = [(pt['lat'], pt['lng']) for pt in coords_list]
            
            # Creamos el polígono geométrico del corral
            corral_polygon = Polygon(polygon_vertices)
            
            # Si el punto está adentro de este corral, ya está, la vaca está a salvo
            if corral_polygon.contains(vaca_point):
                return {"is_inside": True, "alert": False, "ground_name": ground.name}
                
        except Exception as e:
            print(f"Error procesando la geocerca de {ground.name}: {e}")
            continue

    # 3. Si recorrió todos los corrales y no estaba en ninguno, se escapó 
    return {"is_inside": False, "alert": True, "ground_name": "Ninguno (Fuera de límites)"}