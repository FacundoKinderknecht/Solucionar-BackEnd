# ------------------------------------------------------------
# Endpoints de Servicios.
# ------------------------------------------------------------
from fastapi import APIRouter, HTTPException, status

# Placeholder endpoints for servicios. Implement the Servicio model and DB logic when ready.
router = APIRouter(prefix="/servicios", tags=["servicios"])


@router.get("/{servicio_id}")
def read_servicio(servicio_id: int):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Servicios API not implemented yet")


@router.post("/")
def create_servicio():
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Servicios API not implemented yet")
