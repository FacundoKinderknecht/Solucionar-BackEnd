# ------------------------------------------------------------
# Endpoints de Servicios.
# ------------------------------------------------------------
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from database import get_session
from schema.servicios import Servicio

router = APIRouter(prefix="/servicios", tags=["servicios"])

router = APIRouter(prefix="/servicios", tags=["servicios"])
SessionDep = Annotated[Session, Depends(get_session)]

@router.get("/{servicio_id}")
def read_servicio(servicio_id: int, session: SessionDep):
    servicio = session.get(Servicio, servicio_id)
    if not servicio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Servicio no encontrado")
    return servicio

@router.post("/")
async def create_servicio(servicio: Servicio, session: SessionDep):
    session.add(servicio)
    session.commit()
    session.refresh(servicio)
    return servicio
