from enum import Enum


class TokenRejectionReason(str, Enum):
    """Motivo por el que se rechaza un token de acceso.

    Solo se usa en logs y para decidir el código HTTP; nunca se devuelve al cliente.
    """

    MISSING = "missing"
    MALFORMED = "malformed"
    INVALID_SIGNATURE = "invalid_signature"
    EXPIRED = "expired"
    NOT_YET_VALID = "not_yet_valid"
    INVALID_ISSUER = "invalid_issuer"
    INVALID_AUDIENCE = "invalid_audience"
    MISSING_SCOPE = "missing_scope"
    MISSING_IDENTITY = "missing_identity"
    KEYS_UNAVAILABLE = "keys_unavailable"
