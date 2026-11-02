from fastapi import APIRouter, status

from src.database.session import SessionDep
from src.schemas.product import ProductCreate, ProductPublic
from src.services.product import ProductService

router = APIRouter()


@router.post("/", response_model=ProductPublic, status_code=status.HTTP_201_CREATED)
def create_product(product_in: ProductCreate, session: SessionDep):
    """Cadastra um novo produto no sistema. Retorna erro caso o nome já esteja em uso."""
    return ProductService.create(session, product_in)


@router.get("/{product_id}", response_model=ProductPublic)
def read_product(product_id: int, session: SessionDep):
    """Busca os detalhes de um produto específico pelo ID."""
    return ProductService.get(session, product_id)


@router.get("/", response_model=list[ProductPublic])
def read_products(session: SessionDep, skip: int = 0, limit: int = 100):
    """Lista os produtos cadastrados com suporte a paginação."""
    return ProductService.gets(session, skip=skip, limit=limit)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, session: SessionDep):
    """Remove um produto do catálogo."""
    ProductService.delete(session, product_id)
