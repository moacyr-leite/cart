from sqlalchemy import create_engine
from fastapi import Depends
from typing import Annotated, Iterator

from sqlmodel import Session
from src.core.config import settings 

DATABASE_URL = settings.DATABASE_URL 

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True, 
    echo=False          
)

def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session


def begin_write_transaction(session: Session) -> None:
    if session.get_bind().dialect.name == "sqlite":
        session.connection().exec_driver_sql("BEGIN IMMEDIATE")


SessionDep = Annotated[Session, Depends(get_session)]
