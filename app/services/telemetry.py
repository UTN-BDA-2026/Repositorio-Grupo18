from datetime import datetime, timezone
from typing import Optional

from fastapi import BackgroundTasks
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.mongo import telemetry_collection
from app.models.sql import Device
from app.schemas.schemas import TelemetryIngest
from app.workers.behavior import analyze_behavior_window


class TelemetryService:

    @staticmethod
    async def ingest(
        payload: TelemetryIngest,
        db: AsyncSession,
        background_tasks: BackgroundTasks,
    ) -> dict:
    
        # GUARDAR LECTURA EN MONGO
        doc = payload.model_dump()
        doc["timestamp"] = payload.timestamp.replace(tzinfo=timezone.utc)

        result = await telemetry_collection().insert_one(doc)
        inserted_id = str(result.inserted_id)

        # GUARDAR LECTURA EN SQL (actualizar última conexión y porcentaje de batería)
        stmt = (
            update(Device)
            .where(Device.hardware_id == payload.device_hardware_id)
            .values(
                last_seen=datetime.now(timezone.utc),
                battery_pct=payload.battery_pct,
            )
            .returning(Device.id, Device.animal_id)
        )
        result_pg = await db.execute(stmt)
        device_row = result_pg.fetchone()

        # Cada 30 lecturas, lanzar un análisis de comportamiento en segundo plano
        if device_row and device_row.animal_id:
            count = await telemetry_collection().count_documents(
                {"device_hardware_id": payload.device_hardware_id}
            )
            if count % 30 == 0:
                background_tasks.add_task(
                    analyze_behavior_window,
                    animal_id=str(device_row.animal_id),
                    hardware_id=payload.device_hardware_id,
                )

        return {"inserted_id": inserted_id, "status": "ok"}

    @staticmethod
    async def get_recent(
        hardware_id: str,
        limit: int = 100,
    ) -> list[dict]:
        # Retornar las últimas lecturas de un collar desde MongoDB
        cursor = (
            telemetry_collection()
            .find({"device_hardware_id": hardware_id})
            .sort("timestamp", -1)
            .limit(limit)
        )
        docs = await cursor.to_list(length=limit)
        for doc in docs:
            doc["id"] = str(doc.pop("_id"))
        return docs
