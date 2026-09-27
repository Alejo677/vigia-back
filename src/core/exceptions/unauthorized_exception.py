from src.domain.enums.token_rejection_reason import TokenRejectionReason


class UnauthorizedException(Exception):
    """Token ausente o inválido: se responde 401."""

    def __init__(self, message: str, reason: TokenRejectionReason) -> None:
        super().__init__(message)
        self.message = message
        self.reason = reason
