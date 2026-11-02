from collections.abc import Iterator
from contextlib import contextmanager
from typing import Annotated, Any

from fastapi import Depends
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlmodel import Session

from src.core.config import settings


def _enable_sqlite_foreign_keys(dbapi_connection: Any, connection_record: Any) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def build_engine(url: str, **kwargs: Any) -> Engine:
    engine = create_engine(url, **kwargs)
    if engine.dialect.name == "sqlite":
        event.listen(engine, "connect", _enable_sqlite_foreign_keys)
    return engine


engine = build_engine(
    settings.database_url,
    pool_pre_ping=True,
    echo=False,
)


def get_session() -> Iterator[Session]:
    with Session(engine, expire_on_commit=False) as session:
        yield session


def _begin_immediate(session: Session) -> None:
    if session.get_bind().dialect.name == "sqlite":
        session.connection().exec_driver_sql("BEGIN IMMEDIATE")


@contextmanager
def transaction(session: Session) -> Iterator[Session]:
    """Executa o bloco em uma transação de escrita, com commit/rollback automáticos.

    Chamadas aninhadas participam da transação externa (o commit acontece apenas
    no nível mais externo).
    """
    depth = session.info.get("transaction_depth", 0)
    if depth:
        session.info["transaction_depth"] = depth + 1
        try:
            yield session
        finally:
            session.info["transaction_depth"] = depth
        return

    if not session.in_transaction():
        _begin_immediate(session)
    session.info["transaction_depth"] = 1
    try:
        yield session
        session.commit()
    except BaseException:
        session.rollback()
        raise
    finally:
        session.info["transaction_depth"] = 0


SessionDep = Annotated[Session, Depends(get_session)]
