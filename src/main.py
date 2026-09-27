from dotenv import load_dotenv

load_dotenv()

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.v1.api_router import protected_router
from src.api.v1.routers import health
from src.core.configuration.settings import Settings, get_settings
from src.core.exceptions.handlers import register_exception_handlers

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


def create_app(settings: Settings) -> FastAPI:
    """Crea la aplicación FastAPI con middleware, handlers y routers.

    Orden: CORS → Auth (dependencia de `protected_router`) → Errors → Routes.

    Args:
        settings: configuración del backend.

    Returns:
        Aplicación FastAPI.
    """
    app = FastAPI(title="OneWatch API")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins(),
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )
    register_exception_handlers(app)
    app.include_router(health.router)
    app.include_router(protected_router)
    return app


app = create_app(get_settings())
