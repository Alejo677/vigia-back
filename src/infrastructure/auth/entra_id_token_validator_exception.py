from src.domain.enums.token_rejection_reason import TokenRejectionReason


class EntraIdTokenValidatorException(Exception):
    """Única excepción del validador de tokens de Entra ID."""

    def __init__(self, reason: TokenRejectionReason) -> None:
        super().__init__(f"Token rechazado: {reason.value}")
        self.reason = reason
