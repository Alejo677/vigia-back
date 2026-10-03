import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.core.exceptions.authenticate_user_exception import AuthenticateUserException
from src.core.exceptions.conflict_exception import ConflictException
from src.core.exceptions.forbidden_exception import ForbiddenException
from src.core.exceptions.not_found_exception import NotFoundException
from src.core.exceptions.unauthorized_exception import UnauthorizedException
from src.core.exceptions.validation_exception import ValidationException

logger = logging.getLogger(__name__)

UNAUTHORIZED_DETAIL = "No autenticado"
FORBIDDEN_DETAIL = "No tienes acceso a OneWatch"
UNAVAILABLE_DETAIL = "Servicio de identidad no disponible"
INTERNAL_ERROR_DETAIL = "Error interno"


async def _unauthorized_handler(_: Request, __: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=401,
        content={"detail": UNAUTHORIZED_DETAIL},
        headers={"WWW-Authenticate": "Bearer"},
    )


async def _forbidden_handler(_: Request, __: Exception) -> JSONResponse:
    return JSONResponse(status_code=403, content={"detail": FORBIDDEN_DETAIL})


async def _unavailable_handler(_: Request, __: Exception) -> JSONResponse:
    return JSONResponse(status_code=503, content={"detail": UNAVAILABLE_DETAIL})


async def _not_found_handler(_: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": exc.message})  # type: ignore[attr-defined]


async def _conflict_handler(_: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": exc.message})  # type: ignore[attr-defined]


async def _validation_handler(_: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"detail": exc.message, "field": exc.field},  # type: ignore[attr-defined]
    )


async def _internal_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        "❌ Error no controlado",
        extra={"path": request.url.path, "error": type(exc).__name__},
        exc_info=exc,
    )
    return JSONResponse(status_code=500, content={"detail": INTERNAL_ERROR_DETAIL})


def register_exception_handlers(app: FastAPI) -> None:
    """Registra los handlers globales de excepciones de la API.

    Los cuerpos son genéricos: el motivo concreto de un rechazo solo va al log.

    Args:
        app: aplicación FastAPI.
    """
    app.add_exception_handler(UnauthorizedException, _unauthorized_handler)
    app.add_exception_handler(ForbiddenException, _forbidden_handler)
    app.add_exception_handler(AuthenticateUserException, _unavailable_handler)
    app.add_exception_handler(NotFoundException, _not_found_handler)
    app.add_exception_handler(ConflictException, _conflict_handler)
    app.add_exception_handler(ValidationException, _validation_handler)
    app.add_exception_handler(Exception, _internal_error_handler)
