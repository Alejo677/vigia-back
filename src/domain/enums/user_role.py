from enum import Enum


class UserRole(str, Enum):
    """App Roles de OneWatch definidos en Entra ID (ESP-14, Regla 1)."""

    ADMIN = "admin"
    USER = "user"
