from fastapi import APIRouter, Depends

from src.api.v1.routers import auth
from src.core.dependencies.auth import get_current_user

API_V1_PREFIX = "/api/v1"

# Todo /api/v1 exige token de Entra ID por defecto (ESP-14, Regla 5; plan D1).
# Los routers de negocio se incluyen aquí. El de Slack (ESP-11) se registra aparte
# en main.py, con su propia verificación de firma.
protected_router = APIRouter(prefix=API_V1_PREFIX, dependencies=[Depends(get_current_user)])
protected_router.include_router(auth.router)
