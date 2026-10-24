import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.pool import StaticPool  # 🌟 1. IMPORTANTE: Importe o StaticPool

# Garante o carregamento dos modelos na memória
from src.models.product import Product
from src.models.coupon import Coupon
from src.models.cart import Cart, ItemCart

from src.main import app
from src.database.session import get_session

@pytest.fixture(name="engine")
def engine_fixture():
    # 🌟 2. CORREÇÃO: poolclass=StaticPool força a reutilização da mesma conexão em memória!
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Cria todas as tabelas fisicamente
    SQLModel.metadata.create_all(engine)
    
    yield engine
    SQLModel.metadata.drop_all(engine)

@pytest.fixture(name="session")
def session_fixture(engine):
    with Session(engine) as session:
        yield session

@pytest.fixture(name="client")
def client_fixture(session):
    def get_session_override():
        yield session
        
    app.dependency_overrides[get_session] = get_session_override
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
