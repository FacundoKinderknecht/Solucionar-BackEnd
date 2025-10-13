from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from database import get_session
from schema.servicios import Servicio

SessionDep = Annotated[Session, Depends(get_session)]

router = APIRouter()

@router.get("/servicios/{servicio_id}")
async def read_servicio(servicio_id: int, session: SessionDep):
    servicio = session.get(Servicio, servicio_id)
    if not servicio:
        raise HTTPException(status_code=404, detail="Servicio not found")
    return servicio

@router.post("/servicios/")
async def create_servicio(servicio: Servicio, session: SessionDep):
    session.add(servicio)
    session.commit()
    session.refresh(servicio)
    return servicio

@router.put("/servicios/{servicio_id}")
async def update_servicio(servicio_id: int, servicio: Servicio):
    return {"servicio_id": servicio_id, "servicio_name": servicio.name, "servicio_description": servicio.description}