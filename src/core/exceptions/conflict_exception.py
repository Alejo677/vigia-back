class ConflictException(Exception):
    """Operación incompatible con el estado actual del recurso: se responde 409."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
