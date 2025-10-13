from typing import Annotated
from fastapi import Depends
from sqlmodel import SQLModel, create_engine, Session
from dotenv import load_dotenv
import os

load_dotenv()

SQLMODEL_DATABASE_URL = os.getenv("DATABASE_URL")

if SQLMODEL_DATABASE_URL is not None:
    engine = create_engine(SQLMODEL_DATABASE_URL)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

