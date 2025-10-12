from typing import Union, Annotated
from fastapi import FastAPI, Depends
from sqlmodel import SQLModel, Field, Session
import contextlib

from database import engine, get_session, create_db_and_tables


class ServicioBase(SQLModel):
    name: str = Field(index=True)
    description: Union[str, None] = None

class Servicio(ServicioBase, table=True):
    id: int = Field(default=None, primary_key=True)


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

SessionDep = Annotated[Session, Depends(get_session)]
app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return {"message": "Test API"}

@app.get("/servicios/{servicio_id}")
async def read_servicio(servicio_id: int, servicio: Servicio):
    return {"servicio_id": servicio_id, "servicio_name": servicio.name}

@app.post("/servicios/")
async def create_servicio(servicio: Servicio, session: SessionDep):
    session.add(servicio)
    session.commit()
    session.refresh(servicio)
    return servicio

@app.put("/servicios/{servicio_id}")
async def update_servicio(servicio_id: int, servicio: Servicio):
    return {"servicio_id": servicio_id, "servicio_name": servicio.name, "servicio_description": servicio.description}