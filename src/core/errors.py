from enum import Enum

from fastapi import status


class AppError(Enum):
    # 🛒 Cart Errors
    CART_NOT_FOUND = (status.HTTP_404_NOT_FOUND, "Cart not found.")
    COUPON_NOT_FOUND = (status.HTTP_400_BAD_REQUEST, "Invalid or expired coupon.")
    INVALID_COUPON_DISCOUNT = (
        status.HTTP_400_BAD_REQUEST,
        "Coupon discount must be between 0 and 1.",
    )
    ITEM_NOT_FOUND_IN_CART = (
        status.HTTP_404_NOT_FOUND,
        "This product is not present in the specified cart.",
    )
    INVALID_QUANTITY = (
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        "Quantity must be greater than zero.",
    )

    # 📦 Product Errors
    PRODUCT_NOT_FOUND = (status.HTTP_404_NOT_FOUND, "Product not found.")
    PRODUCT_ALREADY_EXISTS = (
        status.HTTP_400_BAD_REQUEST,
        "A product with this name is already registered.",
    )
    PRODUCT_IN_CART = (status.HTTP_409_CONFLICT, "Cannot delete a product reserved in a cart.")
    OUT_OF_STOCK = (status.HTTP_422_UNPROCESSABLE_CONTENT, "Insufficient stock for this product.")

    COUPON_ALREADY_EXISTS = (status.HTTP_400_BAD_REQUEST, "A coupon with this code already exists.")
    CART_EMPTY = (status.HTTP_422_UNPROCESSABLE_CONTENT, "Cannot checkout an empty cart.")

    # 🧾 Order Errors
    ORDER_NOT_FOUND = (status.HTTP_404_NOT_FOUND, "Order not found.")
    ORDER_NOT_CANCELLABLE = (
        status.HTTP_409_CONFLICT,
        "Only paid orders can be cancelled.",
    )
    IDEMPOTENCY_KEY_REUSED = (
        status.HTTP_409_CONFLICT,
        "This idempotency key was already used by another cart.",
    )
    IDEMPOTENCY_KEY_CONFLICT = (
        status.HTTP_409_CONFLICT,
        "This idempotency key was already used with a different request.",
    )
    INVALID_IDEMPOTENCY_KEY = (
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        "Idempotency-Key must be 1-255 characters using letters, numbers, '-', '_', '.', ':'.",
    )

    @property
    def status_code(self) -> int:
        return self.value[0]

    @property
    def detail(self) -> str:
        return self.value[1]


class AppException(Exception):
    """Erro de domínio mapeável para uma resposta HTTP."""

    def __init__(self, error: AppError):
        super().__init__(error.detail)
        self.error = error
