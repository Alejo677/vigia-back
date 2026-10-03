class ValidationException(Exception):
    """Error de validación de un campo concreto: se responde 422 junto al campo afectado."""

    def __init__(self, message: str, field: str) -> None:
        super().__init__(message)
        self.message = message
        self.field = field
