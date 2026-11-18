"""Перевод исключений приложения в HTTP-ответы.

Единственное место, которое знает соответствие «исключение → HTTP-статус».
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from src.core.exceptions import (
    AlreadyExistsError,
    AppError,
    AuthenticationError,
    BusinessRuleError,
    ConfigurationError,
    ExternalServiceError,
    InvalidFileError,
    NotFoundError,
    PermissionDeniedError,
)
from src.core.logger import logger

# Порядок не важен: статус ищется по MRO, поэтому подклассы наследуют статус родителя.
_STATUS_BY_ERROR: dict[type, int] = {
    NotFoundError: status.HTTP_404_NOT_FOUND,
    AlreadyExistsError: status.HTTP_409_CONFLICT,
    BusinessRuleError: status.HTTP_400_BAD_REQUEST,
    InvalidFileError: status.HTTP_400_BAD_REQUEST,
    AuthenticationError: status.HTTP_401_UNAUTHORIZED,
    PermissionDeniedError: status.HTTP_403_FORBIDDEN,
    ExternalServiceError: status.HTTP_502_BAD_GATEWAY,
    ConfigurationError: status.HTTP_500_INTERNAL_SERVER_ERROR,
}


def resolve_status_code(exc: AppError) -> int:
    """Возвращает HTTP-статус для исключения (учитывая иерархию классов)."""
    for cls in type(exc).__mro__:
        if cls in _STATUS_BY_ERROR:
            return _STATUS_BY_ERROR[cls]
    return status.HTTP_500_INTERNAL_SERVER_ERROR


async def app_error_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, AppError):  # для mypy: сюда попадают только AppError
        raise exc
    status_code = resolve_status_code(exc)
    if status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR:
        logger.error(f"{exc.code} on {request.url.path}: {exc.message}")

    headers = (
        {"WWW-Authenticate": "Bearer"} if status_code == status.HTTP_401_UNAUTHORIZED else None
    )
    return JSONResponse(
        status_code=status_code,
        content={"detail": exc.message, "code": exc.code},
        headers=headers,
    )


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Неожиданная ошибка: клиенту — без деталей, traceback уже записан в лог middleware."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error", "code": "internal_error"},
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)
