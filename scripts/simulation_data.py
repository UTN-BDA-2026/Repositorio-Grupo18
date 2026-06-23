"""
Inyecta 1 millón de filas distribuidas en las tablas:
  - users    →  1.000 filas
  - ground   →  5.000 filas
  - animal   →  994.000 filas

Total: 1.000.000 filas
Uso: docker compose exec api python scripts/simulation_data.py
"""
import sys
import os
sys.path.insert(0, "/app")

import asyncio
import random
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import AsyncSessionLocal, engine
from app.models.sql import Base

# =========== CONFIGURACIÓN ===========
# númeroo de filas para las tablas
N_USERS   = 1_000  
N_GROUNDS = 5_000
N_ANIMALS = 994_000
BATCH     = 5_000 

# =========== DATOS PARA SIMULAR ===========
COUNTRIES   = ["Argentina", "Brasil", "Uruguay", "Chile", "Paraguay", "Bolivia"]
ROLES       = ["admin", "users", "vet"]
SPECIES     = ["vaca", "oveja", "cabra", "cerdo", "llama"]
SEXES       = ["M", "F"]

FAKE_HASHED_PW = bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode()

def rand_date(start_year=2018, end_year=2025) -> datetime:
    start = datetime(start_year, 1, 1, tzinfo=timezone.utc)
    end   = datetime(end_year,  12, 31, tzinfo=timezone.utc)
    return start + timedelta(seconds=random.randint(0, int((end - start).total_seconds())))

# =========== FUNCIONES PARA GENERAR LOS DATOS SIMULADOS ===========
def gen_users(n: int) -> list[dict]:
    rows = []
    for i in range(n):
        rows.append({
            "id":              str(uuid.uuid4()),
            "name":            f"Usuario_{i}",
            "email":           f"user_{i}_{uuid.uuid4().hex[:6]}@farm.com",
            "hashed_password": FAKE_HASHED_PW,
            "role":            random.choice(ROLES),
            "country":         random.choice(COUNTRIES),
            "is_active":       random.random() > 0.05,
            "created_at":      rand_date(2018, 2025),
        })
    return rows


def gen_grounds(n: int, user_ids: list[str]) -> list[dict]:
    rows = []
    for i in range(n):
        lat  = round(random.uniform(-40, -22), 6)
        lng  = round(random.uniform(-68, -53), 6)
        rows.append({
            "id":            str(uuid.uuid4()),
            "name":          f"Lote_{i}",
            "geofence":      f'{{"type":"Point","coordinates":[{lng},{lat}]}}',
            "area_hectares": round(random.uniform(10, 500), 2),
            "users_id":      random.choice(user_ids),
            "created_at":    rand_date(2018, 2024),
        })
    return rows


def gen_animals(n: int, user_ids: list[str]) -> list[dict]:
    rows = []
    for _ in range(n):
        rows.append({
            "id":         str(uuid.uuid4()),
            "species":    random.choice(SPECIES),
            "birth_date": rand_date(2018, 2025),
            "sex":        random.choice(SEXES),
            "weight_kg":  round(random.uniform(20, 700), 1),
            "is_active":  random.random() > 0.08,
            "users_id":   random.choice(user_ids),
            "created_at": rand_date(2018, 2025),
        })
    return rows



# =========== INSERTAR DATOS EN LA BASE DE DATOS ===========
async def bulk_insert(db: AsyncSession, table: str, rows: list[dict], batch: int = BATCH):
    if not rows:
        return
    # GENERAR CONSULTA SQL
    keys = list(rows[0].keys())
    cols = ", ".join(keys) 
    values = ", ".join(f":{k}" for k in keys) 
    sql = text(f"INSERT INTO {table} ({cols}) VALUES ({values})")
    '''
    INSERT INTO USERS (id, name, email, ...)
    VALUES (':id', ':name', ':email', ... )
    '''

    total = len(rows)
    for start in range(0, total, batch):
        chunk = rows[start:start + batch] # cortamos la lista 
        await db.execute(sql, chunk) # ejecutamos sql con los valores del chunk
        await db.commit()
    print(f"  {table}: {total}/{total} filas insertadas ✓")


# =========== MAIN ===========

async def seed():
    print("\n=== SmartFarming — Insertar datos simulados en la DB ===\n")

    # Iniciar base de datos y crear tablas si no existen
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:

        # 1. Users
        print(f"Generando {N_USERS:,} usuarios...")
        users = gen_users(N_USERS)
        await bulk_insert(db, "users", users)
        user_ids = [u["id"] for u in users]

        # 2. Grounds
        print(f"\nGenerando {N_GROUNDS:,} lotes...")
        grounds = gen_grounds(N_GROUNDS, user_ids)
        await bulk_insert(db, "ground", grounds)

        # 3. Animals (en bloques para no explotar la RAM)
        print(f"\nGenerando {N_ANIMALS:,} animales (en bloques de {BATCH:,})...")
        inserted = 0
        while inserted < N_ANIMALS:
            chunk_size = min(BATCH * 4, N_ANIMALS - inserted)
            chunk = gen_animals(chunk_size, user_ids)
            await bulk_insert(db, "animal", chunk, batch=BATCH)
            inserted += chunk_size

    print(f"\n✅ Simulación completa: {N_USERS + N_GROUNDS + N_ANIMALS:,} filas totales.\n")


if __name__ == "__main__":
    asyncio.run(seed())
