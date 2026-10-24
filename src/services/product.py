from typing import List
from sqlmodel import Session, select
from src.models.product import Product, ProductCreate
from src.models.cart import ItemCart
from src.core.result import Result
from src.core.errors import AppError
from src.database.session import begin_write_transaction

class ProductService:

    @staticmethod
    def create(session: Session, product_in: ProductCreate) -> Result[Product]:
        """
        Cadastra um novo produto. Garante que o nome seja único 
        para evitar cadastros duplicados acidentais.
        """
        # Verifica se já existe um produto com o mesmo nome
        statement = select(Product).where(Product.name == product_in.name.strip())
        if session.exec(statement).first():
            return Result.fail(AppError.PRODUCT_ALREADY_EXISTS)

        # Mapeia os dados recebidos para a tabela do banco
        db_product = Product(
            name=product_in.name.strip(),
            price=product_in.price,
            amount=product_in.amount
        )
        
        session.add(db_product)
        session.commit()
        session.refresh(db_product)
        return Result.success(db_product)

    @staticmethod
    def get(session: Session, product_id: int) -> Result[Product]:
        """
        Busca um produto específico pelo ID.
        """
        db_product = session.get(Product, product_id)
        if not db_product:
            return Result.fail(AppError.PRODUCT_NOT_FOUND)
        return Result.success(db_product)

    @staticmethod
    def gets(session: Session, skip: int = 0, limit: int = 100) -> List[Product]:
        """
        Lista todos os produtos cadastrados com paginação.
        """
        return session.exec(select(Product).offset(skip).limit(limit)).all()

    @staticmethod
    def delete(session: Session, product_id: int) -> Result[None]:
        """
        Remove um produto do catálogo se ele existir.
        """
        begin_write_transaction(session)
        db_product = session.get(Product, product_id)
        if not db_product:
            session.rollback()
            return Result.fail(AppError.PRODUCT_NOT_FOUND)

        reserved_item = session.exec(
            select(ItemCart).where(ItemCart.product_id == product_id)
        ).first()
        if reserved_item:
            session.rollback()
            return Result.fail(AppError.PRODUCT_IN_CART)

        session.delete(db_product)
        session.commit()
        return Result.success(None)
