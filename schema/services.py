# ------------------------------------------------------------
# Modelos de Servicios (SQLModel).
# ------------------------------------------------------------
from sqlmodel import SQLModel, Field
from typing import Union

class ServicioBase(SQLModel):
    name: str = Field(index=True)
    description: Union[str, None] = None

class Servicio(ServicioBase, table=True):
    id: int = Field(default=None, primary_key=True)
