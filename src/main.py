from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.api.v1.api import api_router
from src.core.errors import AppException

app = FastAPI(
    title="Cart API",
    description="Backend escalável estruturado com FastAPI e SQLModel",
    version="1.0.0",
)

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.error.status_code,
        content={"detail": exc.error.detail},
    )


app.include_router(api_router, prefix="/api/v1")
