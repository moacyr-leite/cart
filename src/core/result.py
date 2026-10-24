from typing import Generic, TypeVar, Optional
from src.core.errors import AppError

T = TypeVar("T")

class Result(Generic[T]):
    def __init__(self, value: Optional[T] = None, error: Optional[AppError] = None):
        self.value = value
        self.error = error

    @property
    def is_success(self) -> bool:
        return self.error is None

    @classmethod
    def success(cls, value: T):
        return cls(value=value)

    @classmethod
    def fail(cls, error: AppError):
        return cls(error=error)
