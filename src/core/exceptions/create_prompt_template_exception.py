class CreatePromptTemplateException(Exception):
    """Error no atribuible al cliente al crear una plantilla de prompt: se responde 502."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
