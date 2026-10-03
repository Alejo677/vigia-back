class DeletePromptTemplateException(Exception):
    """Error no atribuible al cliente al eliminar una plantilla de prompt: se responde 502."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
