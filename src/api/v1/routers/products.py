from fastapi import APIRouter, HTTPException, status
from typing import List

from src.database.session import SessionDep  # Importação partindo de src
from src.models.product import ProductPublic, ProductCreate
from src.services.product import ProductService

router = APIRouter()

@router.post("/", response_model=ProductPublic, status_code=status.HTTP_201_CREATED)
def create_product(product_in: ProductCreate, session: SessionDep):
    """
    Cadastra um novo produto no sistema. 
    Retorna erro caso o nome já esteja em uso.
    """
    result = ProductService.create(session, product_in)
    if not result.is_success:
        raise HTTPException(
            status_code=result.error.status_code, 
            detail=result.error.detail
        )
    return result.value

@router.get("/{product_id}", response_model=ProductPublic)
def read_product(product_id: int, session: SessionDep):
    """
    Busca os detalhes de um produto específico pelo ID.
    """
    result = ProductService.get(session, product_id)
    if not result.is_success:
        raise HTTPException(
            status_code=result.error.status_code, 
            detail=result.error.detail
        )
    return result.value

@router.get("/", response_model=List[ProductPublic])
def read_products(session: SessionDep, skip: int = 0, limit: int = 100):
    """
    Lista os produtos cadastrados com suporte a paginação.
    """
    # Listagens diretas não possuem validações de barreira, retornam a lista pura
    return ProductService.gets(session, skip=skip, limit=limit)

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, session: SessionDep):
    """
    Remove um produto do catálogo.
    """
    result = ProductService.delete(session, product_id)
    if not result.is_success:
        raise HTTPException(
            status_code=result.error.status_code, 
            detail=result.error.detail
        )
    return None
