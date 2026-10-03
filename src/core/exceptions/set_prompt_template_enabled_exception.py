class SetPromptTemplateEnabledException(Exception):
    """Error no atribuible al cliente al activar/desactivar una plantilla: se responde 502."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
