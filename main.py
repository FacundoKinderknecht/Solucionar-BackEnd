from typing import Union, Annotated
from fastapi import FastAPI, Depends
from sqlmodel import Session
import contextlib

from database import get_session, create_db_and_tables
from routers import servicios


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

SessionDep = Annotated[Session, Depends(get_session)]
app = FastAPI(lifespan=lifespan)

app.include_router(servicios.router)

@app.get("/")
async def root():
    return {"message": "Test API"}