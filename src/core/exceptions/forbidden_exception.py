class ForbiddenException(Exception):
    """Token válido sin rol reconocido o con rol insuficiente: se responde 403."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
